// ============================================================================
// Address: 00496b79
// Ghidra name: FUN_00496b79
// Signature: undefined FUN_00496b79(int param_1, int param_2, int param_3, int param_4, int param_5)

void __cdecl FUN_00496b79(int param_1,int param_2,int param_3,int param_4,int param_5)

{
  int iVar1;
  int iVar2;
  int iVar3;
  uint uVar4;
  
  iVar2 = param_1 * 0x7e0 + DAT_005109f8;
  if (*(char *)(iVar2 + 2000) != '\0') {
    iVar1 = *(int *)(iVar2 + 0x10) * 0x8bc + DAT_00568a64;
    iVar3 = *(int *)(iVar2 + 0x20) * 0x34;
    uVar4 = 0;
    iVar2 = iVar3 + iVar1;
    if (*(int *)(iVar3 + 0x7c0 + iVar1) != 0) {
      do {
        iVar1 = *(int *)(iVar2 + 0x7c4);
        FUN_00496cfd((&DAT_00568a94)[uVar4 % 5],1,param_2,
                     (uint *)(param_3 + *(int *)(iVar1 + uVar4 * 8)),
                     (ushort *)(*(int *)(iVar1 + 4 + uVar4 * 8) + param_4),uVar4,param_5,-1,0);
        uVar4 = uVar4 + 1;
      } while (uVar4 < *(uint *)(iVar2 + 0x7c0));
    }
  }
  return;
}



// ============================================================================
