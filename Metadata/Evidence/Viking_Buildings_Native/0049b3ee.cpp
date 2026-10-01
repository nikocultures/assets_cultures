// ============================================================================
// Address: 0049b3ee
// Ghidra name: FUN_0049b3ee
// Signature: undefined FUN_0049b3ee(void * this, int param_1, int param_2, byte * param_3, ushort * param_4)

void __thiscall FUN_0049b3ee(void *this,int param_1,int param_2,byte *param_3,ushort *param_4)

{
  int iVar1;
  
  iVar1 = *(int *)(param_2 + 4);
  if (iVar1 == 0) {
    FUN_00406995((byte *)s_NXBasics__CBobManager__PrintBob__0050726c);
  }
  else if (iVar1 == 1) {
    FUN_0049b437(this,param_1,param_2,param_3,param_4,0);
  }
  else if (iVar1 == 2) {
    FUN_0049b930(this,param_1,param_2,(int)param_3,(byte *)param_4);
  }
  return;
}



// ============================================================================
