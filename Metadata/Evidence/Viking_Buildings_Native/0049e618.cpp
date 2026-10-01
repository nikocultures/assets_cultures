// ============================================================================
// Address: 0049e618
// Ghidra name: FUN_0049e618
// Signature: undefined FUN_0049e618(void * this, int param_1, uint param_2, uint param_3, int param_4, uint * param_5)

void __thiscall
FUN_0049e618(void *this,int param_1,uint param_2,uint param_3,int param_4,uint *param_5)

{
  int *piVar1;
  byte bVar2;
  int iVar3;
  bool bVar4;
  uint uVar5;
  undefined4 uVar6;
  byte *pbVar7;
  uint uVar8;
  ushort *puVar9;
  uint *puVar10;
  uint uVar11;
  int iVar12;
  int iVar13;
  int local_3c;
  int local_38;
  int local_34;
  int local_2c;
  int local_28;
  int local_24;
  int local_20;
  void *local_10;
  uint local_c;
  int local_8;
  
  uVar11 = param_3;
  uVar5 = param_1 - *(int *)((int)this + 4);
  if ((uVar5 < *(uint *)((int)this + 8)) &&
     (piVar1 = (int *)(*(int *)((int)this + 0x24) + uVar5 * 0x18),
     *(int *)(*(int *)((int)this + 0x24) + uVar5 * 0x18) != 0)) {
    local_10 = this;
    FUN_00410360(&local_3c,piVar1 + 1);
    FUN_004103d8(&local_3c,param_4,(int)param_5);
    uVar5 = FUN_004105c3(&local_3c,(int *)(param_3 + 8));
    if ((char)uVar5 != '\0') {
      FUN_00410360(&local_2c,&local_3c);
      uVar6 = FUN_004104d6(&local_2c,(int *)(param_3 + 8));
      param_5 = (uint *)(*(int *)((int)local_10 + 0x2c) + piVar1[5] * 4);
      if (local_38 < 0) {
        param_5 = param_5 + -local_38;
      }
      bVar4 = *(int *)(param_3 + 0x10) <= local_34 + -1 + local_3c;
      param_4 = local_28;
      if (*piVar1 == 1) {
        iVar13 = *(int *)(param_3 + 4);
        iVar12 = 0;
        if (iVar13 == 0) {
          FUN_00406995((byte *)s_NXBasics__CBobManager__PrintBob__005072b0);
        }
        else if (iVar13 == 1) {
          if ((char)uVar6 == '\0') {
            if (0 < local_20) {
              do {
                uVar11 = *param_5;
                param_5 = param_5 + 1;
                if (uVar11 != 0xffffffff) {
                  pbVar7 = (byte *)((uVar11 & 0x3fffff) + *(int *)((int)local_10 + 0x28));
                  puVar9 = (ushort *)
                           (*(int *)(param_3 + 0x28) +
                           ((uVar11 >> 0x16) + local_3c + *(int *)(param_3 + 0x30) * param_4) * 2);
                  while( true ) {
                    bVar2 = *pbVar7;
                    pbVar7 = pbVar7 + 1;
                    if (bVar2 == 0) break;
                    uVar11 = bVar2 & 0x7f;
                    if ((bVar2 & 0x80) == 0) {
                      do {
                        bVar2 = *pbVar7;
                        pbVar7 = pbVar7 + 1;
                        if (bVar2 <= param_2) {
                          *puVar9 = *(ushort *)(*(int *)(DAT_005106e0 + 8) + (uint)*puVar9 * 2);
                        }
                        puVar9 = puVar9 + 1;
                        uVar11 = uVar11 - 1;
                      } while (uVar11 != 0);
                    }
                    else {
                      puVar9 = puVar9 + uVar11;
                    }
                  }
                }
                iVar12 = iVar12 + 1;
                param_4 = param_4 + 1;
              } while (iVar12 < local_20);
            }
          }
          else {
            local_8 = 0;
            if (0 < local_20) {
              do {
                uVar5 = *param_5;
                param_5 = param_5 + 1;
                if (uVar5 != 0xffffffff) {
                  iVar13 = (uVar5 >> 0x16) + local_3c;
                  pbVar7 = (byte *)((uVar5 & 0x3fffff) + *(int *)((int)local_10 + 0x28));
                  if ((iVar13 < 0) || (bVar4)) {
                    iVar12 = *(int *)(uVar11 + 0x30);
                    iVar3 = *(int *)(uVar11 + 0x28);
                    do {
                      bVar2 = *pbVar7;
                      pbVar7 = pbVar7 + 1;
                      if (bVar2 == 0) goto LAB_0049ea92;
                      if ((bVar2 & 0x80) == 0) {
                        param_3 = (uint)bVar2;
                        if (param_3 != 0) {
                          puVar9 = (ushort *)(iVar3 + iVar12 * param_4 * 2 + iVar13 * 2);
                          do {
                            if (((-1 < iVar13) && (iVar13 <= local_24 + -1 + local_2c)) &&
                               (*pbVar7 <= param_2)) {
                              *puVar9 = *(ushort *)(*(int *)(DAT_005106e0 + 8) + (uint)*puVar9 * 2);
                            }
                            iVar13 = iVar13 + 1;
                            puVar9 = puVar9 + 1;
                            pbVar7 = pbVar7 + 1;
                            param_3 = param_3 - 1;
                          } while (param_3 != 0);
                        }
                      }
                      else {
                        iVar13 = iVar13 + (bVar2 & 0x7f);
                      }
                    } while ((iVar13 < 0) || (bVar4));
                  }
                  puVar9 = (ushort *)
                           (*(int *)(uVar11 + 0x28) +
                           (*(int *)(uVar11 + 0x30) * param_4 + iVar13) * 2);
                  while( true ) {
                    bVar2 = *pbVar7;
                    pbVar7 = pbVar7 + 1;
                    if (bVar2 == 0) break;
                    uVar5 = bVar2 & 0x7f;
                    if ((bVar2 & 0x80) == 0) {
                      do {
                        bVar2 = *pbVar7;
                        pbVar7 = pbVar7 + 1;
                        if (bVar2 <= param_2) {
                          *puVar9 = *(ushort *)(*(int *)(DAT_005106e0 + 8) + (uint)*puVar9 * 2);
                        }
                        puVar9 = puVar9 + 1;
                        uVar5 = uVar5 - 1;
                      } while (uVar5 != 0);
                    }
                    else {
                      puVar9 = puVar9 + uVar5;
                    }
                  }
                }
LAB_0049ea92:
                local_8 = local_8 + 1;
                param_4 = param_4 + 1;
              } while (local_8 < local_20);
            }
          }
        }
        else if (iVar13 == 2) {
          local_8 = 0;
          if ((char)uVar6 == '\0') {
            if (0 < local_20) {
              do {
                uVar11 = *param_5;
                param_5 = param_5 + 1;
                if (uVar11 != 0xffffffff) {
                  pbVar7 = (byte *)((uVar11 & 0x3fffff) + *(int *)((int)local_10 + 0x28));
                  puVar10 = (uint *)(*(int *)(param_3 + 0x2c) +
                                    ((uVar11 >> 0x16) +
                                    local_3c + *(int *)(param_3 + 0x30) * param_4) * 4);
                  while( true ) {
                    bVar2 = *pbVar7;
                    pbVar7 = pbVar7 + 1;
                    if (bVar2 == 0) break;
                    local_c = bVar2 & 0x7f;
                    if ((bVar2 & 0x80) == 0) {
                      do {
                        bVar2 = *pbVar7;
                        pbVar7 = pbVar7 + 1;
                        if (bVar2 <= param_2) {
                          uVar11 = *puVar10;
                          uVar5 = (uVar11 >> 0xf & 0x1fffe) / 3;
                          uVar8 = ((uVar11 & 0xff) << 1) / 3;
                          *puVar10 = ((uVar11 >> 7 & 0x1fe) / 3 | uVar5 << 8) << 8 |
                                     (uVar5 + uVar8 >> 4) + uVar8;
                        }
                        puVar10 = puVar10 + 1;
                        local_c = local_c - 1;
                      } while (local_c != 0);
                    }
                    else {
                      puVar10 = puVar10 + local_c;
                    }
                  }
                }
                local_8 = local_8 + 1;
                param_4 = param_4 + 1;
              } while (local_8 < local_20);
            }
          }
          else if (0 < local_20) {
            do {
              uVar11 = *param_5;
              param_5 = param_5 + 1;
              if (uVar11 != 0xffffffff) {
                iVar13 = (uVar11 >> 0x16) + local_3c;
                pbVar7 = (byte *)((uVar11 & 0x3fffff) + *(int *)((int)local_10 + 0x28));
                if ((iVar13 < 0) || (bVar4)) {
                  iVar12 = *(int *)(param_3 + 0x30);
                  iVar3 = *(int *)(param_3 + 0x2c);
                  do {
                    bVar2 = *pbVar7;
                    pbVar7 = pbVar7 + 1;
                    if (bVar2 == 0) goto LAB_0049e895;
                    if ((bVar2 & 0x80) == 0) {
                      local_c = bVar2 & 0x7f;
                      if ((bVar2 & 0x7f) != 0) {
                        puVar10 = (uint *)(iVar3 + iVar12 * param_4 * 4 + iVar13 * 4);
                        do {
                          if (((-1 < iVar13) && (iVar13 <= local_24 + -1 + local_2c)) &&
                             (*pbVar7 <= param_2)) {
                            uVar11 = *puVar10;
                            uVar5 = (uVar11 >> 0xf & 0x1fffe) / 3;
                            uVar8 = ((uVar11 & 0xff) << 1) / 3;
                            *puVar10 = ((uVar11 >> 7 & 0x1fe) / 3 | uVar5 << 8) << 8 |
                                       (uVar5 + uVar8 >> 4) + uVar8;
                          }
                          iVar13 = iVar13 + 1;
                          puVar10 = puVar10 + 1;
                          pbVar7 = pbVar7 + 1;
                          local_c = local_c - 1;
                        } while (local_c != 0);
                      }
                    }
                    else {
                      iVar13 = iVar13 + (bVar2 & 0x7f);
                    }
                  } while ((iVar13 < 0) || (bVar4));
                }
                puVar10 = *(uint **)(param_3 + 0x2c);
                local_c = *(int *)(param_3 + 0x30) * param_4 + iVar13;
                do {
                  puVar10 = puVar10 + local_c;
                  while( true ) {
                    bVar2 = *pbVar7;
                    pbVar7 = pbVar7 + 1;
                    if (bVar2 == 0) goto LAB_0049e895;
                    local_c = bVar2 & 0x7f;
                    if ((bVar2 & 0x80) != 0) break;
                    do {
                      bVar2 = *pbVar7;
                      pbVar7 = pbVar7 + 1;
                      if (bVar2 <= param_2) {
                        uVar11 = *puVar10;
                        uVar5 = (uVar11 >> 0xf & 0x1fffe) / 3;
                        uVar8 = ((uVar11 & 0xff) << 1) / 3;
                        *puVar10 = ((uVar11 >> 7 & 0x1fe) / 3 | uVar5 << 8) << 8 |
                                   (uVar8 + uVar5 >> 4) + uVar8;
                      }
                      puVar10 = puVar10 + 1;
                      local_c = local_c - 1;
                    } while (local_c != 0);
                  }
                } while( true );
              }
LAB_0049e895:
              local_8 = local_8 + 1;
              param_4 = param_4 + 1;
            } while (local_8 < local_20);
          }
        }
      }
    }
  }
  return;
}



// ============================================================================
