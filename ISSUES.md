# Issues for ChromaDB MCP Server

## 🐛 Critical Issues

### Issue #1: Tool Exposure Discrepancy (Priority: High)
**Problem**: Server reports 51 tools, but MCP client only discovers 41 tools (10 tools missing)

**Details**:
- Server log: `51 tools across 13 categories`
- Client discovery: `Discovered 41 tools`
- **Missing**: 10 tools not properly exposed via MCP protocol

**Investigation needed**:
- [ ] Check MCP protocol compatibility for each module
- [ ] Verify `@mcp.tool()` decorator usage
- [ ] Ensure all tools have proper type hints
- [ ] Check for async/sync function mismatches
- [ ] Validate tool registration order

**Potential causes**:
1. Some tools may have incorrect MCP decorator usage
2. Type hint issues preventing proper serialization
3. Async/sync function declaration problems
4. Module import/registration order issues
5. MCP protocol version compatibility

**Test command**:
```bash
cd src
python -c "
from fastmcp_main_modular import FastMCPChromaServer
server = FastMCPChromaServer()
print(f'Total registered tools: {len(server.mcp._tools)}')
for tool_name in sorted(server.mcp._tools.keys()):
    print(f'  - {tool_name}')
"
```

**Expected outcome**: All 51+ server-side tools should be discoverable by MCP clients

---

## 🔧 Technical Debt

### Issue #2: Module Tool Registration Optimization
**Problem**: Some modules may have duplicate or conflicting tool registrations

**Tasks**:
- [ ] Audit all `register_*_tools()` functions
- [ ] Ensure no tool name conflicts between modules
- [ ] Standardize tool naming conventions
- [ ] Add tool registration validation

### Issue #3: MCP Protocol Compliance Check
**Problem**: Need to verify full MCP protocol compliance for all tools

**Tasks**:
- [ ] Validate all tool signatures against MCP spec
- [ ] Check parameter type annotations
- [ ] Ensure proper error handling format
- [ ] Test with multiple MCP clients (VS Code, Claude Desktop)

### Issue #4: Documentation Tool List Sync
**Problem**: README tool count may not match actual implementation

**Tasks**:
- [ ] Auto-generate tool list from code
- [ ] Add tool count validation in CI/CD
- [ ] Sync documentation with actual implementation

---

## 🚀 Enhancement Requests

### Issue #5: Tool Discovery Debugging
**Enhancement**: Add better debugging for tool registration and discovery

**Features**:
- [ ] Tool registration debug mode
- [ ] MCP protocol exposure validation
- [ ] Client-server tool count comparison utility

### Issue #6: Automated Tool Validation
**Enhancement**: Add automated testing for all 51+ tools

**Features**:
- [ ] Unit tests for each tool
- [ ] Integration tests for MCP protocol
- [ ] Tool count validation in test suite

---

## 📋 Action Plan

### Phase 1: Investigation (Priority)
1. **Tool Discovery Debug** - Identify which 10 tools are missing
2. **MCP Protocol Audit** - Check each module for compliance
3. **Registration Order Review** - Ensure proper loading sequence

### Phase 2: Fix Implementation
1. **Fix Missing Tools** - Resolve MCP exposure issues
2. **Standardize Signatures** - Ensure consistent tool signatures
3. **Add Validation** - Implement tool registration validation

### Phase 3: Quality Assurance
1. **Comprehensive Testing** - Test all tools via MCP protocol
2. **Documentation Update** - Sync docs with actual tool count
3. **CI/CD Integration** - Add automated tool count validation

---

## 🎯 Success Criteria

- [ ] **100% Tool Discovery**: All server-side tools discoverable by MCP clients
- [ ] **Zero Discrepancy**: Server count == Client discovery count
- [ ] **Full Functionality**: All 51+ tools working correctly via MCP
- [ ] **Automated Validation**: CI/CD prevents future regressions

---

**Status**: 🔴 Open  
**Milestone**: v1.0 Production Release  
**Estimated Effort**: 2-3 days  
**Impact**: High (affects production readiness)
