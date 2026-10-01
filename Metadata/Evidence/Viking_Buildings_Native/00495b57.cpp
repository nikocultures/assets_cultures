// ============================================================================
// Address: 00495b57
// Ghidra name: FUN_00495b57
// Signature: undefined FUN_00495b57(int * param_1, void * param_2, uint * param_3, uint * param_4, int param_5, void * param_6)

void __cdecl
FUN_00495b57(int *param_1,void *param_2,uint *param_3,uint *param_4,int param_5,void *param_6)

{
  void *pvVar1;
  uint *puVar2;
  bool bVar3;
  char cVar4;
  int iVar5;
  undefined4 uVar6;
  uint uVar7;
  uint *puVar8;
  int iVar9;
  void *pvVar10;
  uint uVar11;
  int *piVar12;
  byte *pbVar13;
  byte *pbVar14;
  void *pvVar15;
  byte *local_240;
  int local_23c [39];
  uint local_1a0;
  int local_19c [80];
  undefined1 local_5c [44];
  int *local_30;
  int local_2c;
  int local_28;
  byte *local_24;
  int local_20;
  byte *local_1c;
  int local_18;
  uint *local_14;
  uint local_10;
  byte local_9;
  uint *local_8;
  
  puVar2 = param_3;
  pvVar15 = (void *)((int)param_1 * 0x7e0 + DAT_005109f8);
  FUN_004316cc((int)pvVar15);
  pbVar14 = (byte *)(*(int *)((int)pvVar15 + 0x10) * 0x8bc + DAT_00568a64);
  local_30 = (int *)((int)param_1 * 0xd0 + DAT_00568b00);
  local_2c = 0;
  local_18 = *(int *)(pbVar14 +
                     (*(uint *)((int)pvVar15 + 8) % *(uint *)(pbVar14 + 0x21c)) * 4 + 0x220);
  if ((char)local_30[0x33] == '\0') {
    if ((param_6 != (void *)0x0) && (*(char *)((int)param_6 + 0x74) == '\0')) {
      param_5 = (*(int *)(pbVar14 + 0x234) * (param_5 + -0x100)) / 0x100 + 0x100;
    }
  }
  else {
    param_5 = FUN_0049b30b();
  }
  if (((*(char *)((int)pvVar15 + 2000) == '\0') && (param_6 != (void *)0x0)) &&
     (iVar5 = FUN_0047d0ef(param_6,(int)param_1), iVar5 != 0)) {
    local_1c = FUN_0049b337(iVar5,*(int *)((int)pvVar15 + 0xc));
    FUN_0049660f((int)param_1,&local_1a0);
    local_10 = 0;
    if (local_1a0 != 0) {
      piVar12 = local_19c + 2;
      do {
        local_8 = (uint *)0xffffffff;
        do {
          if (*(int *)((int)pvVar15 + 0x2c) == 3) {
            FUN_0049bdc8((void *)piVar12[-2],(uint *)piVar12[-1],param_2,*piVar12 + (int)param_3,
                         (uint)((byte *)((int)local_8 + piVar12[1]) + (int)param_4),local_1c,1);
          }
          else {
            FUN_0049bba4((void *)piVar12[-2],piVar12[-1],param_2,*piVar12 + (int)param_3,
                         (byte *)((int)local_8 + piVar12[1]) + (int)param_4,local_1c,1);
          }
          local_8 = (uint *)((int)local_8 + 1);
        } while ((int)local_8 < 2);
        local_10 = local_10 + 1;
        piVar12 = piVar12 + 4;
      } while (local_10 < local_1a0);
    }
  }
  FUN_00496c02((int)param_1,(int)param_2,(int)param_3,(int)param_4,param_5);
  iVar5 = *(int *)((int)pvVar15 + 0x2c);
  if (iVar5 == 3) {
    if (*(char *)((int)pvVar15 + 2000) == '\0') {
      iVar5 = *(int *)(pbVar14 + *(int *)((int)pvVar15 + 0x20) * 4 + 0x238);
      if (*(void **)(pbVar14 + 0x218) != (void *)0x0) {
        FUN_0049b3ee(*(void **)(pbVar14 + 0x218),iVar5,(int)param_2,(byte *)param_3,
                     (ushort *)param_4);
      }
      FUN_00496594(*(void **)(pbVar14 + 0x214),iVar5,local_18,param_5,(int)param_2,param_3,
                   (int)param_4);
      local_10 = 0;
      if (*(int *)(pbVar14 + 0x490) != 0) {
        local_8 = (uint *)0x0;
        do {
          piVar12 = (int *)(*(int *)(pbVar14 + 0x494) + (int)local_8);
          if ((((piVar12[1] != 0) && (*piVar12 == *(int *)((int)pvVar15 + 0x20))) &&
              (piVar12[6] != 0)) &&
             (bVar3 = FUN_004341c0(pvVar15,piVar12[1]), (bool)(char)piVar12[2] == bVar3)) {
            FUN_00496594(*(void **)(pbVar14 + 0x214),
                         piVar12[(int)(((ulonglong)DAT_00510838 / (ulonglong)(uint)piVar12[5]) %
                                      (ulonglong)(uint)piVar12[6]) + 7],local_18,param_5,
                         (int)param_2,(uint *)(piVar12[3] + (int)param_3),piVar12[4] + (int)param_4)
            ;
          }
          local_10 = local_10 + 1;
          local_8 = (uint *)((int)local_8 + 0xe4);
        } while (local_10 < *(uint *)(pbVar14 + 0x490));
      }
      if ((*(byte *)((int)param_6 + 0x72) & 1) != 0) {
        uVar7 = 0;
        local_8 = param_4;
        do {
          local_8 = (uint *)((int)local_8 + 10);
          bVar3 = FUN_004341c0(pvVar15,uVar7);
          if (bVar3) {
            FUN_0040ed30(param_2,*(void **)((int)param_6 + 0x924),(int)param_3,(int)local_8,
                         (byte *)s_ovly__d_005070a8);
          }
          uVar7 = uVar7 + 1;
        } while (uVar7 < 5);
      }
      local_8 = (uint *)0x0;
      do {
        iVar5 = (int)((int)local_8 + *(int *)((int)pvVar15 + 0x20) * 10) * 0x10;
        if ((pbVar14[iVar5 + 0x498] != 0) &&
           (cVar4 = FUN_0043423e(pvVar15,(uint)local_8), cVar4 != '\0')) {
          FUN_00496cfd(*(int *)(pbVar14 + iVar5 + 0x4a4),1,(int)param_2,
                       (uint *)(*(int *)(pbVar14 + iVar5 + 0x49c) + (int)param_3),
                       (ushort *)(*(int *)(pbVar14 + iVar5 + 0x4a0) + (int)param_4),DAT_00510838,
                       param_5,-1,0);
        }
        local_8 = (uint *)((int)local_8 + 1);
      } while (local_8 < (byte *)0xa);
      if (pbVar14[(*(int *)((int)pvVar15 + 0x20) + 0x31) * 0xc] != 0) {
        FUN_004402a3((int)local_5c);
        iVar5 = FUN_0042c214(local_5c,*(undefined4 *)((int)pvVar15 + 0xc),
                             (undefined4 *)((int)pvVar15 + 0x24),1);
        while (iVar5 != -1) {
          uVar6 = FUN_00441aad(iVar5 * 0xc58 + DAT_00510a00);
          if ((char)uVar6 == '\0') {
            iVar5 = *(int *)(pbVar14 + *(int *)((int)pvVar15 + 0x20) * 0xc + 0x250);
            goto LAB_00495f48;
          }
          iVar5 = FUN_0042c392(local_5c);
        }
        iVar5 = *(int *)(pbVar14 + *(int *)((int)pvVar15 + 0x20) * 0xc + 0x254);
LAB_00495f48:
        if (iVar5 != -1) {
          FUN_00496594(*(void **)(pbVar14 + 0x214),iVar5,local_18,param_5,(int)param_2,param_3,
                       (int)param_4);
        }
      }
    }
    else {
      pvVar1 = *(void **)(pbVar14 + 0x214);
      local_1c = *(byte **)(pbVar14 + *(int *)((int)pvVar15 + 0x20) * 4 + 0x238);
      if (pvVar1 == (void *)0x0) {
        return;
      }
      pvVar10 = (void *)(local_18 * 0x30 + DAT_005550e4);
      if (*(int *)((int)pvVar10 + 0x24) != 0) {
        local_24 = (byte *)FUN_00486f3c(pvVar10,param_5 / 2);
        iVar5 = FUN_00439bc2(pvVar1,(int)local_1c);
        if (iVar5 == 4) {
          local_2c = FUN_0049ddf8(pvVar1,(int)local_1c,
                                  (*(short *)((int)pvVar15 + 0x7d2) * 0xff) /
                                  (int)*(short *)((int)pvVar15 + 0x7d4),(int)param_2,param_3,
                                  (uint)param_4,(int)local_24);
        }
      }
    }
  }
  else if ((iVar5 == 1) || (iVar5 == 2)) {
    pbVar13 = *(byte **)((int)pvVar15 + 0x20);
    local_9 = iVar5 == 2;
    local_8 = (uint *)(pbVar14 + (int)pbVar13 * 0x68 + 0x288);
    local_1c = pbVar13;
    local_10 = FUN_00433064((int)pvVar15);
    if (*(char *)((int)pvVar15 + 2000) == '\0') {
      if ((local_9 != 0) && (*(void **)(pbVar14 + 0x218) != (void *)0x0)) {
        FUN_0049b3ee(*(void **)(pbVar14 + 0x218),*(int *)(pbVar14 + (int)pbVar13 * 4 + 0x238),
                     (int)param_2,(byte *)param_3,(ushort *)param_4);
      }
      local_14 = (uint *)0x0;
      if (0 < (int)*local_8) {
        pbVar13 = (byte *)((int)local_8 + 0x10);
        do {
          if ((local_9 == pbVar13[-0xc]) && (*(int *)pbVar13 <= (int)local_10)) {
            FUN_00486f3c((void *)(local_18 * 0x30 + DAT_005550e4),param_5 / 2);
            if (*(int *)(pbVar13 + 4) < (int)local_10) {
              iVar5 = *(int *)(pbVar13 + -4);
              if (iVar5 != -1) {
                uVar7 = 0x100;
LAB_00496078:
                FUN_0049e618(*(void **)(pbVar14 + 0x214),iVar5,uVar7,(uint)param_2,(int)param_3,
                             param_4);
              }
            }
            else if (*(int *)(pbVar13 + -4) != -1) {
              uVar7 = (((int)((local_10 - *(int *)pbVar13) * 100) /
                       (*(int *)(pbVar13 + 4) - *(int *)pbVar13)) * 0xff) / 100;
              iVar5 = *(int *)(pbVar13 + -4);
              goto LAB_00496078;
            }
          }
          local_14 = (uint *)((int)local_14 + 1);
          pbVar13 = pbVar13 + 0x14;
        } while ((int)local_14 < (int)*local_8);
      }
    }
    if (local_9 != 0) {
      if (*(char *)((int)pvVar15 + 2000) == '\0') {
        FUN_00496594(*(void **)(pbVar14 + 0x214),*(int *)(pbVar14 + (int)local_1c * 4 + 0x238),
                     local_18,param_5,(int)param_2,param_3,(int)param_4);
      }
      else {
        pvVar1 = *(void **)(pbVar14 + 0x214);
        local_14 = *(uint **)(pbVar14 + (int)local_1c * 4 + 0x238);
        if (pvVar1 == (void *)0x0) {
          return;
        }
        pvVar10 = (void *)(local_18 * 0x30 + DAT_005550e4);
        if (*(int *)((int)pvVar10 + 0x24) != 0) {
          local_24 = (byte *)FUN_00486f3c(pvVar10,param_5 / 2);
          iVar5 = FUN_00439bc2(pvVar1,(int)local_14);
          if (iVar5 == 4) {
            local_2c = FUN_0049ddf8(pvVar1,(int)local_14,
                                    (*(short *)((int)pvVar15 + 0x7d2) * 0xff) /
                                    (int)*(short *)((int)pvVar15 + 0x7d4),(int)param_2,param_3,
                                    (uint)param_4,(int)local_24);
          }
        }
      }
    }
    local_14 = (uint *)0x0;
    if (0 < (int)*local_8) {
      pbVar13 = (byte *)((int)local_8 + 0x10);
      do {
        if ((local_9 == pbVar13[-0xc]) && (*(int *)pbVar13 <= (int)local_10)) {
          local_24 = (byte *)FUN_00486f3c((void *)(local_18 * 0x30 + DAT_005550e4),param_5 / 2);
          if (*(int *)(pbVar13 + 4) < (int)local_10) {
            if (*(char *)((int)pvVar15 + 2000) == '\0') {
              FUN_00464314(*(void **)(pbVar14 + 0x214),*(int *)(pbVar13 + -8),(int)param_2,param_3,
                           (int)param_4,(int)local_24);
            }
            else {
              local_2c = FUN_0049ddf8(*(void **)(pbVar14 + 0x214),*(int *)(pbVar13 + -8),
                                      (*(short *)((int)pvVar15 + 0x7d2) * 0xff) /
                                      (int)*(short *)((int)pvVar15 + 0x7d4),(int)param_2,param_3,
                                      (uint)param_4,(int)local_24);
            }
          }
          else {
            iVar5 = (int)((local_10 - *(int *)pbVar13) * 100) /
                    (*(int *)(pbVar13 + 4) - *(int *)pbVar13);
            if (*(char *)((int)pvVar15 + 2000) == '\0') {
              FUN_0049da62(*(void **)(pbVar14 + 0x214),*(int *)(pbVar13 + -8),(iVar5 * 0xff) / 100,
                           (int)param_2,param_3,(int)param_4,(int)local_24);
            }
            else {
              FUN_0049e1b7(*(void **)(pbVar14 + 0x214),*(int *)(pbVar13 + -8),
                           (*(short *)((int)pvVar15 + 0x7d2) * 0xff) /
                           (int)*(short *)((int)pvVar15 + 0x7d4),(iVar5 * 0xff) / 100,(int)param_2,
                           (int)param_3,param_4,(int)local_24);
            }
          }
        }
        local_14 = (uint *)((int)local_14 + 1);
        pbVar13 = pbVar13 + 0x14;
      } while ((int)local_14 < (int)*local_8);
    }
    iVar5 = *(int *)(pbVar14 + (int)local_1c * 0x34 + 0x7d8) + (int)param_3;
    local_24 = (byte *)(*(int *)(pbVar14 + (int)local_1c * 0x34 + 0x7dc) + (int)param_4);
    if (param_6 != (void *)0x0) {
      FUN_0047c9ab(param_6,(undefined2 *)((int)pvVar15 + 0x1c),&local_20,'\0');
      FUN_0047c9ab(param_6,(undefined2 *)((int)pvVar15 + 0x24),&local_28,'\0');
      iVar5 = local_28 - local_20;
      local_24 = local_24 + -(int)local_1c;
    }
    iVar9 = FUN_0048b532(*(int *)((int)pvVar15 + 0xc),8);
    if (iVar9 != -1) {
      FUN_00496cfd(iVar9,1,(int)param_2,(uint *)(iVar5 + (int)param_3),
                   (ushort *)(local_24 + (int)param_4),DAT_00510838,param_5,-1,0);
    }
  }
  uVar7 = FUN_0043322f((int)pvVar15);
  if ((char)uVar7 != '\0') {
    local_24 = pbVar14 + *(int *)((int)pvVar15 + 0x20) * 0x34;
    if ((*(int *)(local_24 + 2000) != 0) && (uVar7 = 0, *(int *)(local_24 + 2000) != 0)) {
      do {
        FUN_00496cfd((&DAT_00568aa8)[((int)param_1 + uVar7) % 5],1,(int)param_2,
                     (uint *)(*(int *)(*(int *)(local_24 + 0x7d4) + uVar7 * 8) + (int)param_3),
                     (ushort *)(*(int *)(*(int *)(local_24 + 0x7d4) + 4 + uVar7 * 8) + (int)param_4)
                     ,DAT_00510838,param_5,-1,0);
        uVar7 = uVar7 + 1;
      } while (uVar7 < *(uint *)(local_24 + 2000));
    }
  }
  if ((*(int *)((int)pvVar15 + 0x2c) == 3) || (*(int *)((int)pvVar15 + 0x2c) == 2)) {
    FUN_00496a95((int)param_1);
    uVar7 = 0;
    if (*local_30 != 0) {
      local_24 = *(byte **)((int)pvVar15 + 0x20);
      uVar11 = *(uint *)(pbVar14 + (int)(local_24 + 0x26) * 0x34);
      puVar8 = (uint *)(pbVar14 + (int)(local_24 + 0x26) * 0x34);
      local_14 = puVar8;
      if (uVar11 != 0) {
        do {
          if ((uVar7 < 200) && (*(char *)(uVar7 + 4 + (int)local_30) != '\0')) {
            local_1c = (byte *)(*(int *)(pbVar14 + (int)local_24 * 0x34 + 0x7bc) + uVar7 * 8);
            if (*(int *)(*(int *)(pbVar14 + (int)local_24 * 0x34 + 0x7bc) + -4 + uVar11 * 8) <
                *(int *)(local_1c + 4) + local_2c) break;
            FUN_00496cfd(*(int *)(&DAT_00568a80 + (((int)param_1 + uVar7) % 5) * 4),1,(int)param_2,
                         (uint *)(*(int *)local_1c + (int)param_3),
                         (ushort *)(*(int *)(local_1c + 4) + local_2c + (int)param_4),uVar7,param_5,
                         -1,0);
            puVar8 = local_14;
          }
          uVar11 = *puVar8;
          uVar7 = uVar7 + 1;
        } while (uVar7 < uVar11);
      }
    }
  }
  if (*(char *)((int)pvVar15 + 2000) == '\0') {
    FUN_00496737(param_1,(int *)&local_240);
    local_1c = (byte *)0x0;
    if (local_240 != (byte *)0x0) {
      piVar12 = local_23c + 1;
      do {
        FUN_00496cfd(piVar12[-1],1,(int)param_2,(uint *)(*piVar12 + (int)param_3),
                     (ushort *)(piVar12[1] + (int)param_4),0,param_5,-1,0);
        local_1c = local_1c + 1;
        piVar12 = piVar12 + 4;
      } while (local_1c < local_240);
    }
  }
  FUN_00496b79((int)param_1,(int)param_2,(int)param_3,(int)param_4,param_5);
  if ((param_6 != (void *)0x0) && (*(char *)((int)param_6 + 0x6c) != '\0')) {
    (&DAT_005683c4)[*(int *)((int)pvVar15 + 0xc)] =
         (&DAT_005683c4)[*(int *)((int)pvVar15 + 0xc)] + 1;
  }
  if ((*(byte *)((int)param_6 + 0x72) & 1) != 0) {
    if ((DAT_00568b40 & 1) == 0) {
      DAT_00568b40 = DAT_00568b40 | 1;
      FUN_0040f7d3(&DAT_00568b3c,0xff,0xff,0xff);
      FUN_004e6040(&DAT_0049660e);
    }
    param_5 = -1;
    do {
      param_3 = (uint *)0xffffffff;
      do {
        FUN_0049bba4(*(void **)(pbVar14 + 0x214),
                     *(int *)(pbVar14 + *(int *)((int)pvVar15 + 0x20) * 4 + 0x238),param_2,
                     (int)param_3 + (int)puVar2,(byte *)(param_5 + (int)param_4),&DAT_00568b3c,1);
        param_3 = (uint *)((int)param_3 + 1);
      } while ((int)param_3 < 2);
      param_5 = param_5 + 1;
    } while (param_5 < 2);
    pvVar15 = *(void **)((int)param_6 + 0x924);
    iVar5 = (int)param_4 + 10;
    iVar9 = FUN_0043976c(pvVar15,pbVar14);
    FUN_0040ec57(param_2,pvVar15,(int)puVar2 - iVar9 / 2,iVar5,pbVar14);
  }
  return;
}



// ============================================================================
