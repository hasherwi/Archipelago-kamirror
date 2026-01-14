-- Minimal memory bridge helper (optional).
-- If you already have the standard Archipelago BizHawk Lua socket script, keep using it.
-- This file exists only to document the exact memory ops the Python POC expects:
--
-- read_u8, read_u16_le, write_u8, write_u16_le
--
-- In a typical AP BizHawk setup, these are implemented on the Lua side and exposed to Python.

local mainmemory = mainmemory

function read_u8(addr)
  return mainmemory.read_u8(addr)
end

function read_u16_le(addr)
  return mainmemory.read_u16_le(addr)
end

function write_u8(addr, value)
  mainmemory.write_u8(addr, value)
end

function write_u16_le(addr, value)
  mainmemory.write_u16_le(addr, value)
end
