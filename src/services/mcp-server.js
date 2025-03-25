import { MCPClient } from './mcp-client';

class McpServer {
  constructor() {
    this.client = null;
    this.isInitialized = false;
  }

  async initialize() {
    try {
      this.client = new MCPClient();
      await this.client.connect_to_server('../mcp-server/wea_server.py');
      this.isInitialized = true;
      return true;
    } catch (error) {
      console.error('MCP 服务器初始化失败:', error);
      throw new Error('无法初始化 MCP 服务器，请确保 Python 环境正确配置');
    }
  }

  async processQuery(query) {
    if (!this.isInitialized) {
      throw new Error('MCP 服务器未初始化');
    }

    try {
      const response = await this.client.process_query(query);
      return response;
    } catch (error) {
      console.error('处理查询失败:', error);
      throw new Error('处理查询失败: ' + error.message);
    }
  }

  async cleanup() {
    if (this.client) {
      await this.client.cleanup();
      this.client = null;
    }
  }
}

// 创建并导出单例实例
const mcpService = new McpServer();
export { mcpService }; 