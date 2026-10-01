// ============================================================================
// Address: 0049da62
// Ghidra name: FUN_0049da62
// Signature: undefined FUN_0049da62(void * this, int param_1, uint param_2, int param_3, uint * param_4, int param_5, int param_6)

void __thiscall
FUN_0049da62(void *this,int param_1,uint param_2,int param_3,uint *param_4,int param_5,int param_6)

{
  byte *pbVar1;
  int *piVar2;
  byte bVar3;
  int iVar4;
  int iVar5;
  bool bVar6;
  uint uVar7;
  undefined4 uVar8;
  int iVar9;
  undefined4 *puVar10;
  undefined2 *puVar11;
  byte *pbVar12;
  int iVar13;
  int local_30;
  int local_2c;
  int local_28;
  int local_20;
  int local_1c;
  int local_18;
  int local_14;
  void *local_8;
  
  uVar7 = param_1 - *(int *)((int)this + 4);
  if ((uVar7 < *(uint *)((int)this + 8)) &&
     (piVar2 = (int *)(*(int *)((int)this + 0x24) + uVar7 * 0x18),
     *(int *)(*(int *)((int)this + 0x24) + uVar7 * 0x18) != 0)) {
    local_8 = this;
    FUN_00410360(&local_30,piVar2 + 1);
    FUN_004103d8(&local_30,(int)param_4,param_5);
    uVar7 = FUN_004105c3(&local_30,(int *)(param_3 + 8));
    if ((char)uVar7 != '\0') {
      FUN_00410360(&local_20,&local_30);
      uVar8 = FUN_004104d6(&local_20,(int *)(param_3 + 8));
      param_4 = (uint *)(*(int *)((int)local_8 + 0x2c) + piVar2[5] * 4);
      if (local_2c < 0) {
        param_4 = param_4 + -local_2c;
      }
      bVar6 = *(int *)(param_3 + 0x10) <= local_28 + -1 + local_30;
      param_5 = local_1c;
      if ((*piVar2 == 4) && (iVar9 = *(int *)(param_3 + 4), iVar9 != 0)) {
        if (iVar9 == 1) {
          iVar9 = FUN_0040fc47(param_6);
          if (iVar9 != 0) {
            param_6 = 0;
            if ((char)uVar8 == '\0') {
              if (0 < local_14) {
                do {
                  uVar7 = *param_4;
                  param_4 = param_4 + 1;
                  if (uVar7 != 0xffffffff) {
                    pbVar12 = (byte *)((uVar7 & 0x3fffff) + *(int *)((int)local_8 + 0x28));
                    puVar11 = (undefined2 *)
                              (*(int *)(param_3 + 0x28) +
                              ((uVar7 >> 0x16) + local_30 + *(int *)(param_3 + 0x30) * param_5) * 2)
                    ;
                    while( true ) {
                      bVar3 = *pbVar12;
                      pbVar12 = pbVar12 + 1;
                      if (bVar3 == 0) break;
                      uVar7 = bVar3 & 0x7f;
                      if ((bVar3 & 0x80) == 0) {
                        do {
                          bVar3 = *pbVar12;
                          pbVar1 = pbVar12 + 1;
                          pbVar12 = pbVar12 + 2;
                          if (*pbVar1 <= param_2) {
                            *puVar11 = *(undefined2 *)(iVar9 + (uint)bVar3 * 2);
                          }
                          puVar11 = puVar11 + 1;
                          uVar7 = uVar7 - 1;
                        } while (uVar7 != 0);
                      }
                      else {
                        puVar11 = puVar11 + uVar7;
                      }
                    }
                  }
                  param_6 = param_6 + 1;
                  param_5 = param_5 + 1;
                } while (param_6 < local_14);
              }
            }
            else if (0 < local_14) {
              do {
                uVar7 = *param_4;
                param_4 = param_4 + 1;
                if (uVar7 != 0xffffffff) {
                  iVar13 = (uVar7 >> 0x16) + local_30;
                  pbVar12 = (byte *)((uVar7 & 0x3fffff) + *(int *)((int)local_8 + 0x28));
                  if ((iVar13 < 0) || (bVar6)) {
                    iVar4 = *(int *)(param_3 + 0x30);
                    iVar5 = *(int *)(param_3 + 0x28);
                    do {
                      bVar3 = *pbVar12;
                      pbVar12 = pbVar12 + 1;
                      if (bVar3 == 0) goto LAB_0049dd5f;
                      if ((bVar3 & 0x80) == 0) {
                        uVar7 = (uint)bVar3;
                        if (uVar7 != 0) {
                          puVar11 = (undefined2 *)(iVar5 + iVar4 * param_5 * 2 + iVar13 * 2);
                          do {
                            if (((-1 < iVar13) && (iVar13 <= local_18 + -1 + local_20)) &&
                               (pbVar12[1] <= param_2)) {
                              *puVar11 = *(undefined2 *)(iVar9 + (uint)*pbVar12 * 2);
                            }
                            iVar13 = iVar13 + 1;
                            puVar11 = puVar11 + 1;
                            pbVar12 = pbVar12 + 2;
                            uVar7 = uVar7 - 1;
                          } while (uVar7 != 0);
                        }
                      }
                      else {
                        iVar13 = iVar13 + (bVar3 & 0x7f);
                      }
                    } while ((iVar13 < 0) || (bVar6));
                  }
                  puVar11 = (undefined2 *)
                            (*(int *)(param_3 + 0x28) +
                            (*(int *)(param_3 + 0x30) * param_5 + iVar13) * 2);
                  while( true ) {
                    bVar3 = *pbVar12;
                    pbVar12 = pbVar12 + 1;
                    if (bVar3 == 0) break;
                    uVar7 = bVar3 & 0x7f;
                    if ((bVar3 & 0x80) == 0) {
                      do {
                        bVar3 = *pbVar12;
                        pbVar1 = pbVar12 + 1;
                        pbVar12 = pbVar12 + 2;
                        if (*pbVar1 <= param_2) {
                          *puVar11 = *(undefined2 *)(iVar9 + (uint)bVar3 * 2);
                        }
                        puVar11 = puVar11 + 1;
                        uVar7 = uVar7 - 1;
                      } while (uVar7 != 0);
                    }
                    else {
                      puVar11 = puVar11 + uVar7;
                    }
                  }
                }
LAB_0049dd5f:
                param_6 = param_6 + 1;
                param_5 = param_5 + 1;
              } while (param_6 < local_14);
            }
          }
        }
        else if (((iVar9 == 2) && (iVar9 = FUN_0040fd04(param_6), iVar9 != 0)) &&
                (param_6 = 0, 0 < local_14)) {
          do {
            uVar7 = *param_4;
            param_4 = param_4 + 1;
            if (uVar7 != 0xffffffff) {
              iVar13 = (uVar7 >> 0x16) + local_30;
              pbVar12 = (byte *)((uVar7 & 0x3fffff) + *(int *)((int)local_8 + 0x28));
              if ((iVar13 < 0) || (bVar6)) {
                iVar4 = *(int *)(param_3 + 0x30);
                iVar5 = *(int *)(param_3 + 0x2c);
                do {
                  bVar3 = *pbVar12;
                  pbVar12 = pbVar12 + 1;
                  if (bVar3 == 0) goto LAB_0049dc37;
                  if ((bVar3 & 0x80) == 0) {
                    uVar7 = (uint)bVar3;
                    if (uVar7 != 0) {
                      puVar10 = (undefined4 *)(iVar5 + iVar4 * param_5 * 4 + iVar13 * 4);
                      do {
                        if (((-1 < iVar13) && (iVar13 <= local_18 + -1 + local_20)) &&
                           (pbVar12[1] <= param_2)) {
                          *puVar10 = *(undefined4 *)(iVar9 + (uint)*pbVar12 * 4);
                        }
                        iVar13 = iVar13 + 1;
                        puVar10 = puVar10 + 1;
                        pbVar12 = pbVar12 + 2;
                        uVar7 = uVar7 - 1;
                      } while (uVar7 != 0);
                    }
                  }
                  else {
                    iVar13 = iVar13 + (bVar3 & 0x7f);
                  }
                } while ((iVar13 < 0) || (bVar6));
              }
              puVar10 = (undefined4 *)
                        (*(int *)(param_3 + 0x2c) +
                        (*(int *)(param_3 + 0x30) * param_5 + iVar13) * 4);
              while( true ) {
                bVar3 = *pbVar12;
                pbVar12 = pbVar12 + 1;
                if (bVar3 == 0) break;
                uVar7 = bVar3 & 0x7f;
                if ((bVar3 & 0x80) == 0) {
                  do {
                    bVar3 = *pbVar12;
                    pbVar1 = pbVar12 + 1;
                    pbVar12 = pbVar12 + 2;
                    if (*pbVar1 <= param_2) {
                      *puVar10 = *(undefined4 *)(iVar9 + (uint)bVar3 * 4);
                    }
                    puVar10 = puVar10 + 1;
                    uVar7 = uVar7 - 1;
                  } while (uVar7 != 0);
                }
                else {
                  puVar10 = puVar10 + uVar7;
                }
              }
            }
LAB_0049dc37:
            param_6 = param_6 + 1;
            param_5 = param_5 + 1;
          } while (param_6 < local_14);
        }
      }
    }
  }
  return;
}



// ============================================================================
