# ChromaDB MCP Tools Package
# Modular architecture for 45+ ChromaDB tools organized by category

from .monitoring import register_monitoring_tools
from .basic_operations import register_basic_operations_tools
from .collection_management import register_collection_management_tools
from .history_conversation import register_history_conversation_tools
from .analytics_optimization import register_analytics_optimization_tools
from .backup_maintenance import register_backup_maintenance_tools
from .data_extraction import register_data_extraction_tools
from .collection_inspection import register_collection_inspection_tools
from .collection_confirmation import register_collection_confirmation_tools
from .pdf_learning import register_pdf_learning_tools
from .html_learning import register_html_learning_tools
from .data_integrity_management import register_data_integrity_tools

__all__ = [
    # Monitoring tools (5 tools)
    'register_monitoring_tools',
    
    # Basic operations tools (4 tools)
    'register_basic_operations_tools',
    
    # Collection management tools (5 tools)
    'register_collection_management_tools',
    
    # History & conversation tools (3 tools)
    'register_history_conversation_tools',
    
    # Analytics & optimization tools (3 tools)
    'register_analytics_optimization_tools',
      # Backup & maintenance tools (4 tools)
    'register_backup_maintenance_tools',
    
    # Data extraction tools (2 tools)
    'register_data_extraction_tools',
    
    # Collection inspection tools (5 tools)
    'register_collection_inspection_tools',
    
    # Collection confirmation & safety tools (4 tools)
    'register_collection_confirmation_tools',
      # PDF learning & file processing tools (3 tools)
    'register_pdf_learning_tools',
    
    # HTML learning & web content processing tools (2 tools)
    'register_html_learning_tools',
    
    # Data integrity & quality management tools (4 tools)
    'register_data_integrity_tools',
]

def register_all_tools(mcp, db_manager):
    """全ツールを一括登録する便利関数"""
    register_monitoring_tools(mcp, db_manager)
    register_basic_operations_tools(mcp, db_manager)
    register_collection_management_tools(mcp, db_manager)
    register_history_conversation_tools(mcp, db_manager)
    register_analytics_optimization_tools(mcp, db_manager)
    register_backup_maintenance_tools(mcp, db_manager)
    register_data_extraction_tools(mcp, db_manager)
    register_collection_inspection_tools(mcp, db_manager)
    register_collection_confirmation_tools(mcp, db_manager)
    register_pdf_learning_tools(mcp, db_manager)
    register_html_learning_tools(mcp, db_manager)
    register_data_integrity_tools(mcp, db_manager)  # 新しいデータ整合性ツール
