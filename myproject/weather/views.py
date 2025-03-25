import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from asgiref.sync import async_to_sync
from .mcp_handler import MCPHandler

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name='dispatch')
class WeatherQueryView(APIView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mcp_handler = MCPHandler()
        logger.info("WeatherQueryView initialized")

    def post(self, request, *args, **kwargs):
        """同步处理POST请求"""
        try:
            logger.info(f"Received query request: {request.data}")
            query = request.data.get('query')
            if not query:
                logger.warning("Empty query received")
                return Response(
                    {'error': '查询内容不能为空'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 使用同步方式调用异步函数
            response = async_to_sync(self._process_query)(query)
            return Response({'response': response})
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def _process_query(self, query: str) -> str:
        """异步处理查询"""
        logger.info(f"Processing query: {query}")
        try:
            response = await self.mcp_handler.process_query(query)
            logger.info(f"Query processed successfully: {response}")
            return response
        except Exception as e:
            logger.error(f"Error in _process_query: {str(e)}", exc_info=True)
            raise

    def delete(self, request, *args, **kwargs):
        """清理资源"""
        try:
            async_to_sync(self.mcp_handler.cleanup)()
            return Response({'message': '资源已清理'})
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )





