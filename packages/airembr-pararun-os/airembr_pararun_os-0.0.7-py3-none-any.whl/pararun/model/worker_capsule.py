from typing import Optional, Callable, Any
from pydantic import BaseModel

from pararun.config import Config
from pararun.consumer.batcher import BulkedResult
from pararun.model.batcher import BatcherConfig
from pararun.model.status import DispatchStatus
from pararun.model.transport_context import TransportContext
from pararun.service.fallback import FallbackManager
from pararun.service.invokers import invoke, async_invoke
from pararun.service.logger.log_handler import get_logger, log_handler

logger = get_logger(__name__)
fallback = FallbackManager()
config = Config()


class FunctionCapsule(BaseModel):
    module: str
    name: str


class PublishPayload(BaseModel):
    capsule: 'WorkerCapsule'
    job_tag: str
    context: TransportContext
    headers: dict
    options: Optional[dict] = {}


class WorkerCapsule(BaseModel):
    function: FunctionCapsule
    args: tuple
    kwargs: dict
    guard: Optional[FunctionCapsule] = None

    def _allow(self, context: TransportContext):
        if not self.guard:
            return True
        return invoke(context, self.guard.module, self.guard.name, self.args, self.kwargs)

    async def run(self, context: TransportContext):

        if not self._allow(context):
            return None

        result = await async_invoke(context, self.function.module, self.function.name, self.args, self.kwargs)

        return result

    @staticmethod
    def _convert(result):
        for _result in result:
            if isinstance(_result, BaseModel):
                yield _result.model_dump(mode='json')
            else:
                yield _result


    async def _invoke(self, batcher, context):

        # Run as asyncio task without batcher
        result = await self.run(context)

        if isinstance(result, BulkedResult):
            result = result.result

        if not batcher:
            return result

        # With batcher
        if not isinstance(result, list):
            result = [result]

        result = list(self._convert(result))

        batcher_module, batcher_name = batcher.get_module_and_function()
        return await async_invoke(context, batcher_module, batcher_name, [result])

    async def push(self,
                   job_tag: str,
                   context: TransportContext,
                   batcher: Optional[BatcherConfig] = None,
                   adapter=None,
                   options: Optional[dict] = None,
                   on_error: Optional[Callable] = None,
                   queued: Optional[bool] = True
                   ) -> DispatchStatus:

        serialized_args = adapter.adapter_protocol.publish(self.args, on_error)
        self.args = adapter.adapter_protocol.consumer(serialized_args)

        serialized_kwargs = adapter.adapter_protocol.publish(self.kwargs, on_error)
        self.kwargs = adapter.adapter_protocol.consumer(serialized_kwargs)

        if on_error:
            on_error_function = lambda payload, e: on_error(payload, "No adapter", e)
        else:
            on_error_function = None

        assert isinstance(context, TransportContext)

        if not self._allow(context):
            return DispatchStatus(result=None, logs=log_handler.collection, status=403, error=None)

        try:

            logger.debug(f"Running inline. job tag: {job_tag}")
            result = await self._invoke(batcher, context)
            return DispatchStatus(result=result, logs=log_handler.collection, status=200, error=None)


        # On connection error
        except Exception as e:
            fallback.set_error_mode(str(e))
            logger.error(str(e))
            publish_payload = PublishPayload(
                capsule=self,
                job_tag=job_tag,
                context=context,
                headers={},
                options={}
            )
            if on_error_function:
                try:
                    on_error_function(publish_payload)
                except Exception as e:
                    logger.error(str(e))
            return DispatchStatus(result=None, logs=log_handler.collection, status=200, error=None)
