"""
FastMCP Main Server - モジュール分割版
全機能保持、ファイル分割のみ
元905行 → メイン35行 + モジュール群
"""

import sys
from pathlib import Path

# パス設定
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

# 基本インポート
from fastmcp import FastMCP
from modules.core_manager import ChromaDBManager
from modules.basic_tools import register_basic_tools
from modules.search_tools import register_search_tools
from modules.storage_tools import register_storage_tools
from modules.analysis_tools import register_analysis_tools
from modules.management_tools import register_management_tools
from modules.data_tools import register_data_tools
from modules.system_tools import register_system_tools
from modules.extraction_tools import register_extraction_tools
from modules.backup_tools import register_backup_tools
from modules.learning_tools import register_learning_tools
from modules.monitoring_tools import register_monitoring_tools
from modules.inspection_tools import register_inspection_tools
from modules.integrity_tools import register_integrity_tools

# メインサーバークラス
class FastMCPChromaServer:
    def __init__(self):
        self.mcp = FastMCP("chroma")
        self.manager = ChromaDBManager()
        self.register_all_tools()
    
    def register_all_tools(self):
        """全ツールモジュールを登録 - 51ツール目標"""
        register_basic_tools(self.mcp, self.manager)
        register_search_tools(self.mcp, self.manager)
        register_storage_tools(self.mcp, self.manager)
        register_analysis_tools(self.mcp, self.manager)
        register_management_tools(self.mcp, self.manager)
        register_data_tools(self.mcp, self.manager)
        register_system_tools(self.mcp, self.manager)
        register_extraction_tools(self.mcp, self.manager)
        register_backup_tools(self.mcp, self.manager)
        register_learning_tools(self.mcp, self.manager)
        register_monitoring_tools(self.mcp, self.manager)
        register_inspection_tools(self.mcp, self.manager)
        register_integrity_tools(self.mcp, self.manager)
    
    def run(self):
        """サーバー起動"""
        self.mcp.run()

def main():
    server = FastMCPChromaServer()
    server.run()

if __name__ == "__main__":
    main()
