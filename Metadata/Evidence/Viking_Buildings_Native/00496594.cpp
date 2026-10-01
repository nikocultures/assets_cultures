// ============================================================================
// Address: 00496594
// Ghidra name: FUN_00496594
// Signature: undefined FUN_00496594(void * param_1, int param_2, int param_3, int param_4, int param_5, uint * param_6, int param_7)

void __cdecl
FUN_00496594(void *param_1,int param_2,int param_3,int param_4,int param_5,uint *param_6,int param_7
            )

{
  uint uVar1;
  int iVar2;
  void *this;
  
  if ((param_1 != (void *)0x0) &&
     (this = (void *)(param_3 * 0x30 + DAT_005550e4), *(int *)((int)this + 0x24) != 0)) {
    uVar1 = FUN_00486f3c(this,param_4 / 2);
    iVar2 = FUN_00439bc2(param_1,param_2);
    if (iVar2 == 1) {
      FUN_00463aee(param_1,param_2,param_5,(int)param_6,param_7,uVar1);
    }
    else {
      iVar2 = FUN_00439bc2(param_1,param_2);
      if (iVar2 == 4) {
        FUN_00464314(param_1,param_2,param_5,param_6,param_7,uVar1);
      }
    }
  }
  return;
}



// ============================================================================
