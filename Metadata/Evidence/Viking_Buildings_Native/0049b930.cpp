// ============================================================================
// Address: 0049b930
// Ghidra name: FUN_0049b930
// Signature: undefined FUN_0049b930(void * this, int param_1, int param_2, int param_3, byte * param_4)

void __thiscall FUN_0049b930(void *this,int param_1,int param_2,int param_3,byte *param_4)

{
  int *piVar1;
  ushort uVar2;
  byte bVar3;
  int iVar4;
  int iVar5;
  bool bVar6;
  uint uVar7;
  uint uVar8;
  uint uVar9;
  uint uVar10;
  uint *puVar11;
  uint *puVar12;
  uint *puVar13;
  int iVar14;
  int local_3c;
  int local_38;
  int local_34;
  int local_30;
  int local_2c;
  int local_28;
  int local_24;
  int iStack_20;
  uint local_14;
  void *local_10;
  int local_8;
  
  uVar7 = param_1 - *(int *)((int)this + 4);
  if (uVar7 < *(uint *)((int)this + 8)) {
    piVar1 = (int *)(*(int *)((int)this + 0x24) + uVar7 * 0x18);
    if ((*piVar1 != 0) && (*piVar1 == 2)) {
      local_2c = piVar1[1];
      local_28 = piVar1[2];
      local_24 = piVar1[3];
      iStack_20 = piVar1[4];
      local_10 = this;
      FUN_004103d8(&local_2c,param_3,(int)param_4);
      uVar7 = FUN_004105c3(&local_2c,(int *)(param_2 + 8));
      if ((char)uVar7 != '\0') {
        local_3c = local_2c;
        local_38 = local_28;
        local_34 = local_24;
        local_30 = iStack_20;
        FUN_0041046d(&local_3c,(int *)(param_2 + 8));
        puVar13 = (uint *)(*(int *)((int)local_10 + 0x2c) + piVar1[5] * 4);
        if (local_28 < 0) {
          puVar13 = puVar13 + -local_28;
        }
        bVar6 = *(int *)(param_2 + 0x10) <= local_24 + -1 + local_2c;
        local_8 = local_38;
        if ((*(int *)(param_2 + 4) == 2) && (uVar2 = 0, 0 < local_30)) {
          do {
            uVar7 = *puVar13;
            puVar13 = puVar13 + 1;
            if (uVar7 != 0xffffffff) {
              iVar14 = (uVar7 >> 0x16) + local_2c;
              param_4 = (byte *)((uVar7 & 0x3fffff) + *(int *)((int)local_10 + 0x28));
              if ((iVar14 < 0) || (bVar6)) {
                iVar4 = *(int *)(param_2 + 0x30);
                iVar5 = *(int *)(param_2 + 0x2c);
                do {
                  bVar3 = *param_4;
                  param_4 = param_4 + 1;
                  if (bVar3 == 0) goto LAB_0049bb8a;
                  if ((bVar3 & 0x80) == 0) {
                    local_14 = (uint)bVar3;
                    if (local_14 != 0) {
                      puVar11 = (uint *)(iVar5 + iVar4 * local_8 * 4 + iVar14 * 4);
                      do {
                        if ((-1 < iVar14) && (iVar14 <= local_34 + -1 + local_3c)) {
                          uVar7 = *puVar11;
                          uVar8 = (uVar7 >> 0xf & 0x1fffe) / 3;
                          uVar9 = ((uVar7 & 0xff) << 1) / 3;
                          *puVar11 = ((uVar7 >> 7 & 0x1fe) / 3 | uVar8 << 8) << 8 |
                                     (uVar8 + uVar9 >> 4) + uVar9;
                        }
                        iVar14 = iVar14 + 1;
                        puVar11 = puVar11 + 1;
                        local_14 = local_14 - 1;
                      } while (local_14 != 0);
                    }
                  }
                  else {
                    iVar14 = iVar14 + (bVar3 & 0x7f);
                  }
                } while ((iVar14 < 0) || (bVar6));
              }
              puVar11 = *(uint **)(param_2 + 0x2c);
              uVar7 = *(int *)(param_2 + 0x30) * local_8 + iVar14;
              while( true ) {
                puVar11 = puVar11 + uVar7;
                bVar3 = *param_4;
                param_4 = param_4 + 1;
                if (bVar3 == 0) break;
                uVar7 = bVar3 & 0x7f;
                if (((bVar3 & 0x80) == 0) &&
                   (puVar12 = puVar11, local_14 = uVar7, (bVar3 & 0x7f) != 0)) {
                  do {
                    uVar8 = *puVar12;
                    uVar9 = (uVar8 >> 0xf & 0x1fffe) / 3;
                    uVar10 = ((uVar8 & 0xff) << 1) / 3;
                    *puVar12 = ((uVar8 >> 7 & 0x1fe) / 3 | uVar9 << 8) << 8 |
                               (uVar10 + uVar9 >> 4) + uVar10;
                    local_14 = local_14 - 1;
                    puVar12 = puVar12 + 1;
                  } while (local_14 != 0);
                }
              }
            }
LAB_0049bb8a:
            uVar2 = uVar2 + 1;
            local_8 = local_8 + 1;
          } while ((int)(uint)uVar2 < local_30);
        }
      }
    }
  }
  return;
}



// ============================================================================
