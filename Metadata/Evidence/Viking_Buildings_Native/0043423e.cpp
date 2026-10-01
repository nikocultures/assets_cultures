// ============================================================================
// Address: 0043423e
// Ghidra name: FUN_0043423e
// Signature: undefined1 FUN_0043423e(void * this, uint param_1)

undefined1 __thiscall FUN_0043423e(void *this,uint param_1)

{
  undefined1 uVar1;
  
  if (((int)param_1 < 0) || (9 < param_1)) {
    uVar1 = 0;
  }
  else {
    uVar1 = *(undefined1 *)(param_1 + 0x7bc + (int)this);
  }
  return uVar1;
}



// ============================================================================
