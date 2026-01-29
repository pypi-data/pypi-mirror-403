from typing import Any, Dict, Optional, Type

from velocity.aws.handlers import context as VelocityContext


class ContextFactory:
    def __init__(self, context_class: Optional[Type[VelocityContext.Context]] = None):
        self.context_class = context_class or VelocityContext.Context

    def create(
        self,
        *,
        aws_event: Dict[str, Any],
        aws_context: Any,
        args: Dict[str, Any],
        postdata: Dict[str, Any],
        response: Any,
        session: Optional[Dict[str, Any]],
    ) -> VelocityContext.Context:
        return self.context_class(
            aws_event=aws_event,
            aws_context=aws_context,
            args=args,
            postdata=postdata,
            response=response,
            session=session,
        )
