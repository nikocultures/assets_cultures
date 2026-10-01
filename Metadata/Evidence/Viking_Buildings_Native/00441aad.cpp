// ============================================================================
// Address: 00441aad
// Ghidra name: FUN_00441aad
// Signature: undefined4 FUN_00441aad(int param_1)

undefined4 __fastcall FUN_00441aad(int param_1)

{
  undefined4 uVar1;
  
  uVar1 = 0;
  if ((*(char *)(param_1 + 0xb50) != '\0') || (*(char *)(param_1 + 0xb51) != '\0')) {
    uVar1 = 1;
  }
  return uVar1;
}



// ============================================================================
