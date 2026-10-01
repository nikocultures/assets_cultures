// ============================================================================
// Address: 004341c0
// Ghidra name: FUN_004341c0
// Signature: bool FUN_004341c0(void * this, int param_1)

bool __thiscall FUN_004341c0(void *this,int param_1)

{
  bool bVar1;
  
  if (param_1 < 5) {
    bVar1 = *(int *)((int)this + param_1 * 4 + 0x7a8) != 0;
  }
  else {
    bVar1 = false;
  }
  return bVar1;
}



// ============================================================================
