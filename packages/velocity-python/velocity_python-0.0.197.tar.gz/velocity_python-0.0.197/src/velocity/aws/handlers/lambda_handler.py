import copy
import json
import logging
import os
import pprint
import time
from typing import Optional

from velocity.aws.handlers.base_handler import BaseHandler
from velocity.aws.handlers.context_factory import ContextFactory
from velocity.aws.handlers.response import Response
from velocity.logging import configure_logging
from . import context

configure_logging()
logger = logging.getLogger(__name__)


class LambdaHandler(BaseHandler):
    user_table: Optional[str] = None
    def __init__(
        self, 
        aws_event, 
        aws_context, 
        context_factory: Optional[ContextFactory] = None,
        context_class: type = context.Context,
    ):
        self.start = time.time()
        super().__init__(
            aws_event,
            aws_context,
            context_factory=context_factory,
            context_class=context_class,
        )


    def beforeAction(self, tx, context):
        # Enhanced activity tracking
        stop_processing = self._enhanced_before_action(tx, context)
        if stop_processing is True:
            return 
        logger.debug("starting LamdaHandler.beforeAction")

        
        context.perf.start("get_cognito_user")
        self.cognito_user = context.get_cognito_user(self.aws_event)
        context.perf.log("get_cognito_user")
        self.current_user = {}

        logger.debug("DEBUG: !!! cognito_user %s", self.cognito_user)
        session = context.session() or {}
        try:
            email_address = self.cognito_user["attributes"]["email"]
            session["email_address"] = email_address
        except Exception:
            logger.warning("Unable to read email from Cognito user", exc_info=True)

        logger.info(
            "Starting action",
            extra={
                "action": context.action(),
                "context_args": context.args(),
                "summary": self._summarize_postdata(context.postdata()),
                "session_email": session.get("email_address"),
            },
        )

        if not self.user_table:
            logger.warning(
                "user_table not configured; skipping DB lookup for %s",
                session.get("email_address"),
            )
            raise Exception(
                "User table not configured; cannot validate user [Config]"
            )
        context.perf.start("user lookup")
        row = tx.table(self.user_table).find(
            {"email_address": session.get("email_address")}
        )
        context.perf.log("user lookup")
        if not row:
            raise Exception(
                "A valid user with permission is required to access this function [DB]"
            )
        self.current_user = row.to_dict()
         
        temp = copy.deepcopy(context.postdata())
        temp["payload"].pop("cognito_user", None)
        logger.debug(
            "Events.OnAction %s",
            temp.get("action"),
            extra={"payload": pprint.pformat(temp)},
        )

    def afterAction(self, tx, context):
        stop_processing = self._enhanced_after_action(tx, context)
        if stop_processing is True:
            return

        logger.debug("starting LamdaHandler.afterAction")

        self.end = time.time()
        logger.info(
            "Completed action",
            extra={
                "action": context.action(),
                "duration": self.end - self.start,
            },
        )

    def onError(self, tx, context, exc, tb):
        stop_processing = self._enhanced_error_handler(tx, context, exc, tb)
        if stop_processing is True:
            return
        logger.debug("starting LamdaHandler.aws_api_activity")
        request_id = getattr(self.aws_context, "aws_request_id", None)
        logger.error(
            "Unhandled exception for action %s",
            context.action(),
            exc_info=exc,
            extra={"request_id": request_id},
        )

        logger.debug("starting BackOfficeEvents.onError")

        temp = copy.deepcopy(context.postdata())
        logger.debug("starting BackOfficeEvents.log")
        temp["payload"].pop("cognito_user", None)
        logger.error(
            "Events.OnError %s",
            temp.get("action"),
            extra={"payload": pprint.pformat(temp), "traceback": tb},
        )
        logger.debug("Ending BackOfficeEvents.OnError Done")
            
    def serve(self, tx):
        response = Response()
        req_params = self.aws_event.get("queryStringParameters") or {}
        local_context = self.create_context(
            args=req_params,
            postdata={},
            response=response,
            session=None,
        )
        local_context.perf.start("parse body")
        postdata = local_context.parse_postdata()
        local_context.update_postdata(postdata)
        local_context.configure_perf(postdata=postdata)
        local_context.perf.log("parse body")

        # Determine action from postdata or query parameters
        action = postdata.get("action") or req_params.get("action")
        
        # Get the list of actions to execute
        actions = self.get_actions_to_execute(action)
        
        # Use BaseHandler's execute_actions method
        local_context.perf.start("execute_actions total (serve)")
        try:
            self.execute_actions(tx, local_context, actions)
        except Exception as e:
            self.handle_error(tx, local_context, e)
        local_context.perf.log("execute_actions total (serve)")

        local_context.perf.start("response.render")
        rendered = local_context.response().render()
        local_context.perf.log("response.render")

        return rendered

    def track(self, tx, data=None, user=None, context_obj=None):
        context_obj = context_obj or self.context
        session = context_obj.session() if context_obj else {}
        sanitized_payload = context.sanitize_tracking_payload(data or {})
        sanitized_payload.update(
            {
                "source_ip": session.get("source_ip"),
                "referer": session.get("referer"),
                "user_agent": session.get("user_agent"),
                "device_type": session.get("device_type"),
            }
        )

        email = context_obj.resolve_tracking_email(user)

        if email:
            sanitized_payload["sys_modified_by"] = email
        elif not sanitized_payload.get("sys_modified_by"):
            sanitized_payload["sys_modified_by"] = session.get("email_address") or "system"

        if not email:
            raise Exception(f"Tracking email could not be resolved for tracking.")

        table_name = context_obj.get_tracking_table(email)

        try:
            tx.table(table_name).insert(sanitized_payload)
        except Exception as exc:  # pragma: no cover - best effort logging
            self.log(tx, f"Failed to write tracking record: {exc}", "track")

    def validate(self, user_required=True):
        session = self.context.session() if self.context else {}
        if user_required:
            try:
                attrs = self.cognito_user["attributes"]
                assert attrs
                assert attrs["email"]
                assert attrs["sub"]
                assert session["sub"]
                assert session["sub"] == attrs["sub"]
            except:
                raise Exception("User Authentication Error [Cognito]")
        else:
            try:
                if not session["sub"]:
                    # User is not signed in. If user_required
                    # is false, then simply return
                    return
                attrs = self.cognito_user["attributes"]
                assert attrs
                assert attrs["email"]
                assert attrs["sub"]
                assert session["sub"]
                assert session["sub"] == attrs["sub"]
            except:
                raise Exception("User Authentication Error [Cognito]")

    def _summarize_postdata(self, postdata):
        """Extract key fields from postdata for logging without storing entire payload"""
        if not postdata:
            return {}

        summary = {
            "action": postdata.get("action"),
            "payload_keys": (
                list(postdata.get("payload", {}).keys())
                if isinstance(postdata.get("payload"), dict)
                else None
            ),
        }

        # Add size info
        try:
            summary["payload_size_bytes"] = len(json.dumps(postdata.get("payload", {})))
        except:
            summary["payload_size_bytes"] = 0

        return summary