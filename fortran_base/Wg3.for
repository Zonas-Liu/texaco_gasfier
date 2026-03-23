      SUBROUTINE GASIFIER
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      INCLUDE 'COMMON.00'      
      INCLUDE 'COMMON.01'      
      INCLUDE 'COMMON.02'
      INCLUDE 'COMMON.03'

      DIMENSION DALT(11)
C *** DALT(I)代表某小室矩阵DMAT(J,I)的所有列元素的上一次值组成的数组
	SUM_RI=0.0
      DO 1991  I=NZRA,NZRE
      DO 13 K=1,NVWS
C *** NVWS代表每个小室的方程数(也即变量数)
	   DMAT(K,I)=0.D00
	   DO 13 L=1,NVWS
		  AMAT(K,L,I)=0.D00
		  BMAT(K,L,I)=0.D00
		  CMAT(K,L,I)=0.D00
 13   CONTINUE

      K=0
  53  CONTINUE
CCCCCCCCCCCCCCCCCCCCC  	
	FEM(I)=0.0D00
	DO 777 J=1,NGAS
777	FEM(I)=FEM(I)+FEMF(J,I)      
      DO 82 II=NZRA,NZRE
      U0(II)=FEM(II)*RAG*T(II)/(PWK*AT(II))
  82  CONTINUE

	DO 778 J=1,NGAS
778	Y(J)=FEMF(J,I)/FEM(I)

	CALL XMASS
      CALL ENTFED
      CALL ENTKOL
CCCCCCCCCCCCCCCCCCCC
	IF(KTRLR.EQ.1) THEN
	RXK1=XK1(I)
	RXK2=XK2(I) 
	RXK3=XK3(I)
	RXK4=XK4(I)
	RXK5=XK5(I)
	RXK6=XK6(I)

      RA1=A1(I)
      RA2=A2(I)
	RA3=A3(I)
	RA4=A4(I)
	RA5=A5(I)
	RRI=RI(I)
	IF(K.EQ.0) RAC(I)=RRI
	ELSE
	RXK1=0.0
	RXK2=0.0 
	RXK3=0.0
	RXK4=0.0
	RXK5=0.0

      RA1=0.0
      RA2=0.0
	RA3=0.0
	RA4=0.0
	RA5=0.0
	RRI=0.0
	IF(K.EQ.0) RAC(I)=RRI
	ENDIF
CCCCCCCCCCCCCCCCCCCCCC
      RPHI=PHI(I)
C *** RA1代表某小室中颗粒中碳 C+H2O->CO+H2的反应速率
C *** RA2代表某小室中颗粒中碳 C+2H2->CH4的反应速率
C *** RA3代表某小室中颗粒中碳 C+O2->CO+CO2的反应速率
C *** RA4代表某小室中颗粒中碳 C+CO2->2CO的反应速率
C ***************************************************************
C 得到DMAT函数矢量各具体结果（质量平衡）
C	GAS NUMBER: 1-O2,2-CH4,3-CO,4-CO2,5-H2S,6-H2,7-N2,8-H2O
C				9-CARBON,10-ASH
C #########################################################################################
C O2的来源是:(1)挥发份释出的O2=========+RO2(I)
C            (2)上部小室流进的O2=======+FEMF(1,I-1)或者直接供入的氧气FEEDO2
C O2的消耗是:(1)本小室流出的O2======-FEMF(1,I)
C            (2)CO+1/2O2->CO2反应所消耗的O2====-RXKJ*FEMF(3,I)*FEMF(1,I)/(2.*FEM(I)**2)
C            (3)H2+1/2O2->H2O反应所消耗的O2====-RXHJ*FEMF(6,I)**2.0*FEMF(1,I)/(2.0*FEM(I)**3)
C            (4)挥发份燃烧所消耗的O2======-XOCH4*RVCH4(I)
C                                        -XOH2*RH2(I)
C                                        -XOH2*RVH2(I)
C                                        -RCO(I)*0.5
C                                        -1.16525*RVTAR(I)
C            (5)C+O2->CO+CO2反应所消耗的O2===-RA3*FEMF(1,I)/(FEM(I)*RPHI)
C#########################################################################################
 	DMAT(1,I)=RO2(I)+FEEDO2(I)
      IF (I.NE.NZRA) THEN 
	   DMAT(1,I)=DMAT(1,I)+FEMF(1,I-1)
	ENDIF
      DMAT(1,I)=DMAT(1,I)-FEMF(1,I)
	DMAT(1,I)=DMAT(1,I)
     &          -0.0*XOCH4*RVCH4(I)-0.0*XOH2*(RH2(I)+RVH2(I))
c     &          -XOCH4*RVCH4(I)-0.0*XOH2*(RH2(I)+RVH2(I))
     &          -0.0*XOCO*RCO(I)-XOTAR*RVTAR(I)

	DMAT(1,I)=DMAT(1,I)
     &          -RXK1/2.0
     &          -RXK2/2.0
     &		  -RXK6*2.0
	DMAT(1,I)=DMAT(1,I)
     &          -RA3/RPHI
               
C #########################################################################################
C CH4的来源是:(1)挥发份燃烧和直接释放的CH4=======+RVCH4(I)
C             (2)C+2H2->CH4反应所生成的CH4======+RA2*(FEMF(6,I)/FEM(I)-
C                                               SQRT(FEMF(9,I)/FEM(I)/P(I)/CS_KEQ2))
C             (3)上部小室流进的CH4===============+FEMF(9,I-1)
C CH4的消耗是:(1)本小室流出的CH4=================-FEMF(9,I) 
C	        (2)CH4+H2O->CO+3H2反应所消耗的CH4==-RXJWFEMFJ*FEMF(9,I)*FEMF(8,I)/(FEM(I)**2.0)
C             (3)本小室由射流区向回流区气体扩散流出的CH4========
C               -(FEMF(9,I)/FEM(I)-FR(9,I)/FRM(I))*ATJ(I)*DELZ(I)*11.0*P(I)/(RAG*TGJ(I))
C #########################################################################################
      DMAT(2,I)=0.0+RVCH4(I)
     &		 +KCHECK*RVCH4(I)
      IF (I.NE.NZRA) THEN 
	   DMAT(2,I)=DMAT(2,I)+FEMF(2,I-1)
	ENDIF
	DMAT(2,I)=DMAT(2,I)-FEMF(2,I)
	
	DMAT(2,I)=DMAT(2,I)
     &          -RXK5
     &		  -RXK6
     	DMAT(2,I)=DMAT(2,I)
     &          +RA2
  
C #########################################################################################
C RCO(I) SHOUD NOT BE INCLUDED, BECAUSE BURN OUT
C CO的来源是:(1)C+CO2->2CO 反应所生成的CO====+2.*RA4*FEMF(4,I)/FEM(I)
C            (2)C+H2O->CO+H2反应所生成的CO==+RA1*(FEMF(8,I)/FEM(I)-
C                                         FEMF(6,I)/FEM(I)*FEMF(3,I)/FEM(I)*P(I)/CS_KEQ1)
C            (3)C+O2->CO+CO2反应所生成的CO==+RA3*(2.-2./RPHI)*FEMF(1,I)/FEM(I)
C	       (4)CO2+H2->CO+H2O反应所生成的CO==+RXSH2J*FEMF(4,I)*FEMF(6,I)/(FEM(I)**2.0)
C	       (5)CH4+H2O->CO+3H2反应所生成的CO=+RXJWFEMFEMF*FEMF(9,I)*FEMF(8,I)/(FEM(I)**2.0)
C            (6)上部小室流进的CO==============+FEMF(3,I-1)
C CO的消耗是:(1)本小室流出的CO====-FEMF(3,I)
C            (2)CO+1/2O2->CO2反应所消耗的CO=-RXKJ*FEMF(3,I)*FEMF(1,I)/(FEM(I)**2.0)
C	       (3)CO+H2O->CO2+H2反应所消耗的CO=-RXSH1J*FEMF(3,I)*FEMF(8,I)/(FEM(I)**2.0)
C #########################################################################################
      DMAT(3,I)=0.0+RCO(I)
     &		 +KCHECK*RCO(I)
      IF (I.NE.NZRA) THEN 
	   DMAT(3,I)=DMAT(3,I)+FEMF(3,I-1)
	ENDIF
      
      DMAT(3,I)=DMAT(3,I)-FEMF(3,I)
	DMAT(3,I)=DMAT(3,I)
     &   	      -RXK1
     &          -RXK3
     &          +RXK4
     &          +RXK5
     	DMAT(3,I)=DMAT(3,I)
     &          +RA1
     &          +RA3*(2.0-2.0/RPHI)
     &          +RA4*2.0
     &          -RA5
      
C #########################################################################################
C CO2的来源是:(1)挥发份燃烧和直接释放的CO2=====+RCO2(I)+XCOCH*RVCH4(I)+RCO(I)+RVTAR(I)
C             (2)CO+1/2O2->CO2反应所生成的CO2=+RXKJ*FEMF(3,I)*FEMF(1,I)/(FEM(I)**2)
C             (3)CO+H2O->CO2+H2反应所生成的CO2=+RXSH1J*FEMF(3,I)*FEMF(8,I)/(FEM(I)**2.0)
C             (4)C+O2->CO+CO2 反应所生成的CO2=+RA3*(2./RPHI-1.)*FEMF(1,I)/FEM(I)
C             (5)上部小室流进的CO2=============+FEMF(4,I-1)     
C CO2的消耗是:(1)本小室流出的CO2 ==============-FEMF(4,I)
C	        (2)CO2+H2->CO+H2O反应所消耗的CO2=====-RXSH2J*FEMF(4,I)*FEMF(6,I)/(FEM(I)**2.0)
C			(3)C+CO2->2CO反应所消耗的CO2=====-RA4*FEMF(4,I)/FEM(I)
C             (4)本小室由射流区向回流区气体扩散流出的CO2========
C                -(FEMF(4,I)/FEM(I)-FR(4,I)/FRM(I))*ATJ(I)*DELZ(I)*P(I)/(RAG*TGJ(I))
C #########################################################################################
      DMAT(4,I)=RCO2(I)+FEDCO2(I)	!加入CO2
      IF (I.NE.NZRA) THEN 
	   DMAT(4,I)=DMAT(4,I)+FEMF(4,I-1)
	ENDIF

	DMAT(4,I)=DMAT(4,I)-FEMF(4,I)
      DMAT(4,I)=DMAT(4,I)	
     &          +0.0*XCOCH*RVCH4(I)+XCTAR_CO*(0.0*RCO(I)+RVTAR(I))
c     &          +XCOCH*RVCH4(I)+XCTAR_CO*(0.0*RCO(I)+RVTAR(I))

      DMAT(4,I)=DMAT(4,I)
     &          +RXK1
     &          +RXK3
     &          -RXK4
     &		  +RXK6
      DMAT(4,I)=DMAT(4,I)
     &          +RA3*(2.0/RPHI-1.0)
     &          -RA4
     &		  +RA5
      DMAT(4,I)=DMAT(4,I)/1.2			!20080324

C #########################################################################################
C H2S的来源是:(1)挥发份直接释放的H2S======+RH2S(I)
C             (2)上部小室流进的H2S========+FEMF(5,I-1)     
C H2S的消耗是:(1)本小室流出的H2S==========-FEMF(5,I) 
C             (2)本小室由射流区向回流区气体扩散流出的H2S========
C             -(FEMF(5,I)/FEM(I)-FR(5,I)/FRM(I))*ATJ(I)*DELZ(I)*11.0*P(I)/(RAG*TGJ(I))
C #########################################################################################
      DMAT(5,I)=RH2S(I)
      IF (I.NE.NZRA) THEN 
	   DMAT(5,I)=DMAT(5,I)+FEMF(5,I-1)
	ENDIF

      DMAT(5,I)=DMAT(5,I)-FEMF(5,I)
	          
C #########################################################################################
C H2的来源是:(1)挥发份直接释放的H2================+RH2(I)+RVH2(I)
C            (2)C+H2O->CO+H2反应所生成的H2========+RA1*(FEMF(8,I)/FEM(I)-
C                                         FEMF(6,I)/FEM(I)*FEMF(3,I)/FEM(I)*P(I)/CS_KEQ1)
C	       (3)CO+H2O->CO2+H2反应所生成的H2======+RXSH1J*FEMF(3,I)*FEMF(8,I)/(FEM(I)**2.0)
C	       (4)CH4+H2O->CO+3H2反应所生成的H2=====+3.0*RXJWFEMFJ*FEMF(9,I)*FEMF(8,I)/(FEM(I)**2.0)
C            (5)上部小室流进的H2==================+FEMF(6,I-1)
C H2的消耗是:(1)本小室流出的H2 ===================-FEMF(6,I)
C            (2)C+2H2->CH4反应所消耗的H2==========-2.0*RA2*(FEMF(6,I)/FEM(I)-
C                                                 SQRT(FEMF(9,I)/FEM(I)/P(I)/CS_KEQ2))
C            (3)H2+0.5O2->H2O反应所消耗的H2=======-RXHJ*FEMF(6,I)**2.0*FEMF(1,I)/(FEM(I)**3)
C	       (4)CO2+H2->CO+H2O反应所消耗的H2======-RXSH2J*FEMF(4,I)*FEMF(6,I)/(FEM(I)**2.0)
C            (5)本小室由射流区向回流区气体扩散流出的H2========
C            -(FEMF(6,I)/FEM(I)-FR(6,I)/FRM(I))*ATJ(I)*DELZ(I)*11.0*P(I)/(RAG*TGJ(I))
C #########################################################################################
      DMAT(6,I)=RVH2(I)+RH2(I)
C      DMAT(6,I)=0.0
     &		 +KCHECK*(RVH2(I)+RH2(I))
      IF (I.NE.NZRA) THEN 
	   DMAT(6,I)=DMAT(6,I)+FEMF(6,I-1)
	ENDIF
	DMAT(6,I)=DMAT(6,I)-FEMF(6,I)

	DMAT(6,I)=DMAT(6,I)
     &          -RXK2
     &          +RXK3
     &          -RXK4
     &          +RXK5*3.0

	DMAT(6,I)=DMAT(6,I)
     &          +RA1
     &          -RA2*2.0
     &		  +RA5
      DMAT(6,I)=DMAT(6,I)*1.02		!20080324

C #########################################################################################
C N2的来源是:(1)挥发份释出的N2==================+REN2(I)
C            (2)上部小室流进的N2或供入的N2======+FEMF(7,I-1) OR +FEEDN2
C N2的消耗是:(1)本小室流出的N2===================-FEMF(7,I)
C            (2)本小室由射流区向回流区气体扩散流出的N2========
C -(FEMF(7,I)/FEM(I)-FR(7,I)/FRM(I))*ATJ(I)*DELZ(I)*P(I)/(RAG*TGJ(I))
C #########################################################################################
 	DMAT(7,I)=REN2(I)+FEEDN2(I)
      IF (I.NE.NZRA) THEN 
	   DMAT(7,I)=DMAT(7,I)+FEMF(7,I-1)
	ENDIF

      DMAT(7,I)=DMAT(7,I)-FEMF(7,I)

C #########################################################################################
C H2O的来源是:(1)挥发份燃烧和直接释放的H2O=======+XHOCH*RVCH4(I)+XHOH2*RH2(I)+
C                                               +RVH2(I)*XHOH2+RVH2O(I)+0.3445*RVTAR(I)
C             (2)供入的煤中所含的H2O=============+FEDH2O(I)
C             (3)H2+0.5O2->H2O反应所生成的H2O====+RXHJ*FEMF(6,I)**2.0*FEMF(1,I)/(FEM(I)**3)
C	        (4)CO2+H2->CO+H2O反应所生成的H2O===+RXSH2J*FEMF(4,I)*FEMF(6,I)/(FEM(I)**2.0)
C             (5)上部小室流进的H2O===============+FEMF(8,I-1)
C H2O的消耗是:(1)本小室流出的H2O=================-FEMF(8,I) 
C             (2)C+H2O->CO+H2反应所消耗的H2O=====-RA1*(FEMF(8,I)/FEM(I)-
C                                                FEMF(6,I)/FEM(I)*FEMF(3,I)/FEM(I)*P(I)/CS_KEQ1)
C	        (3)CO+H2O->CO2+H2反应所消耗的H2O===-RXSH1J*FEMF(3,I)*FEMF(8,I)/(FEM(I)**2.0) 
C	        (4)CH4+H2O->CO+3H2反应所消耗的H2O==-RXJWFEMFJ*FEMF(9,I)*FEMF(8,I)/(FEM(I)**2.0)
C             (5)本小室由射流区向回流区气体扩散流出的H2O========
C                -(FEMF(8,I)/FEM(I)-FR(8,I)/FRM(I))*ATJ(I)*DELZ(I)*P(I)/(RAG*TGJ(I))
C #########################################################################################
 	DMAT(8,I)=RVH2O(I)+FEDH2O(I)
      IF (I.NE.NZRA) THEN 
	   DMAT(8,I)=DMAT(8,I)+FEMF(8,I-1)
	ENDIF      
	DMAT(8,I)=DMAT(8,I)-FEMF(8,I)
	DMAT(8,I)=DMAT(8,I)
     &  +0.0*XHOCH*RVCH4(I)+0.0*XHOH2*(RH2(I)+RVH2(I))+XHTAR*RVTAR(I)
c     &  +XHOCH*RVCH4(I)+0.0*XHOH2*(RH2(I)+RVH2(I))+XHTAR*RVTAR(I)

      DMAT(8,I)=DMAT(8,I)
     &          +RXK2
     &          -RXK3
     &          +RXK4
     &          -RXK5
     &		  +RXK6*2.0
	DMAT(8,I)=DMAT(8,I)
     &          -RA1
     &		  -RA5

C #########################################################################################
C C---  MASS BALANCE OF SOLIDS
C	RIMAX=WFC(I)+WE(I-1)*X(I-1)-WE(I)*X(I)+XMS(I)*X(I)/TRZ(I)
C	IF(RRI.LT.RIMAX) THEN
 	DMAT(NSGP,I)=WFC(I)+WFA(I)+KCHECK*RVTAR(I)*XMTAR
      IF (I.NE.NZRA) THEN 
	   DMAT(NSGP,I)=DMAT(NSGP,I)+WE(I-1)
	ENDIF      
	DMAT(NSGP,I)=DMAT(NSGP,I)-WE(I)-RRI
C	ELSE
C	DMAT(NSGP,I)=WFC(I)+WFA(I)+WE(I-1)+XMS(I)/TRZ(I)-WE(I)-RIMAX
C	ENDIF
C #########################################################################################
C C---  MASS BALANCE OF CARBON <  X(I)  > (UNIT: KG/S)
C C的来源是:(1)加入的C===========================+WFC
C           (2)由I-1小室下流到I小室的颗粒中所含C====+WE(I-1)*X(I-1)
C C的消耗是:(1)由I小室下流到I+1小室的灰中所含C====-WE(I)*X(I)
C           (2)被渣层所捕获部分灰颗粒的含碳量C====-BSMS*ELAS/(PI*DIAMETER_F(I))*YELTA(I)*XP(I)/(1-XP(I))
C           (3)碳的总消耗速率=============-RRI
C #########################################################################################
C	LIZHENG ADDED ON FEB. 12, LIMITATION OF CARBON MASS
C	IF(RRI.LT.RIMAX) THEN
 	DMAT(NSGP1,I)=WFC(I)
      IF (I.NE.NZRA) THEN 
	   DMAT(NSGP1,I)=DMAT(NSGP1,I)+WE(I-1)*X(I-1)
     &                              -RVTAR(1)*XMTAR*X(I-1)*KCHECK
	ENDIF      
	DMAT(NSGP1,I)=DMAT(NSGP1,I)-WE(I)*X(I)-RRI
     &                           +RVTAR(1)*XMTAR*X(I)*KCHECK
C	ELSE
C 	DMAT(NSGP1,I)=RRI-RIMAX
C	ENDIF

C---  ENERGY BALANCE FOR ITH CELL
C---  ENERGY BALANCE IN J
C---  HENTH & DHDT ORDER:
C         (1)       O2                               DHDT  (1)
C         (2)       CH4                                    (2)
C         (3)       CO                                     (3)
C         (4)       CO2                                    (4)
C         (5)       H2S                                    (5)
C         (6)       H2                                     (6)
C         (7)       N2                                     (7)
C         (8)       H2O                                    (8)
C         (9)       C                                      (9)
C         (10)      ASH                                    (10)

C 第10个方程---------能量平衡方程!!!
	IF(KTRLT.EQ.1) THEN
      IF (I.NE.NZRA) THEN
          DMAT(NVWS,I)=FEMF(1,I-1)*HENTH(1,I-1)
     &                +FEMF(2,I-1)*HENTH(2,I-1)
     &                +FEMF(3,I-1)*HENTH(3,I-1)
     &                +FEMF(4,I-1)*HENTH(4,I-1)
     &                +FEMF(5,I-1)*HENTH(5,I-1)
     &                +FEMF(6,I-1)*HENTH(6,I-1)
     &                +FEMF(7,I-1)*HENTH(7,I-1)
     &                +FEMF(8,I-1)*HENTH(8,I-1)
	ELSE
         DMAT(NVWS,I)=0.0
	ENDIF
C 上部I-1小室流入I小室的气体能量
      DMAT(NVWS,I)=DMAT(NVWS,I)
     &             +RVCH4(I)*ENTHP(2,'G   ',TFEED_SL,PFEED_SL)
     &             +(RH2(I)+RVH2(I))*ENTHP(6,'G   ',TFEED_SL,PFEED_SL)
     &             +RVH2O(I)*HFH2O(I)
     &             +RO2(I)*ENTHP(1,'G   ',TFEED_SL,PFEED_SL)
     &             +REN2(I)*ENTHP(7,'G   ',TFEED_SL,PFEED_SL)
     &             +RCO(I)*ENTHP(3,'G   ',TFEED_SL,PFEED_SL)
     &             +RCO2(I)*ENTHP(4,'G   ',TFEED_SL,PFEED_SL)
     &             +RVTAR(I)*9.3D06
     &             +RH2S(I)*ENTHP(5,'G   ',TFEED_SL,PFEED_SL)     
C I小室中由煤中水分和挥发份释放的气体的能量
      DMAT(NVWS,I)=DMAT(NVWS,I)+FEEDO2(I)*FEEDH(1,I)
     &             +FEEDN2(I)*FEEDH(2,I)+FEDCO2(I)*FEEDH(3,I)	!加入CO2
C I小室中供入的空气的能量
      DMAT(NVWS,I)=DMAT(NVWS,I)
     &			   -(FEMF(1,I)*HENTH(1,I)
     &                +FEMF(2,I)*HENTH(2,I)
     &                +FEMF(3,I)*HENTH(3,I)
     &                +FEMF(4,I)*HENTH(4,I)
     &                +FEMF(5,I)*HENTH(5,I)
     &                +FEMF(6,I)*HENTH(6,I)
     &                +FEMF(7,I)*HENTH(7,I)
     &                +FEMF(8,I)*HENTH(8,I))
C 由I小室流出到I+1小室的气体能量
C---  ENTERRING PARTICLE FLOW 固体颗粒
      DMAT(NVWS,I)=DMAT(NVWS,I)+WFC(I)*FEDPH(1,I)
     &             +WFA(I)*FEDPH(2,I)+FEDH2O(I)*HFH2O(I)
C 小室I中供入的固体的能量 
      IF (I.NE.NZRA) THEN
      DMAT(NVWS,I)=DMAT(NVWS,I)+WE(I-1)*
     &	     (X(I-1)*HENTH(9,I-1)+(1.0-X(I-1))*HENTH(10,I-1))
     &                         -RVTAR(1)*XMTAR*KCHECK*
     &	     (X(I-1)*HENTH(9,I-1)+(1.0-X(I-1))*HENTH(10,I-1))
	ENDIF
C流入I小室的固体能量
      DMAT(NVWS,I)=DMAT(NVWS,I)-WE(I)*
     &	     (X(I)*HENTH(9,I)+(1.0-X(I))*HENTH(10,I))
     &						 +RVTAR(1)*XMTAR*KCHECK*
     &	     (X(I)*HENTH(9,I)+(1.0-X(I))*HENTH(10,I))
C流入I小室的固体能量

	IF(T(I).GT.TW) THEN
	QKW(I)=WDKR(T(I),TW)*AR(I)*DELZ(I)*(T(I)-TW)
	ELSE
	QKW(I)=0.0
	ENDIF
      DMAT(NVWS,I)=DMAT(NVWS,I)-QKW(I)

C=============================
C	ENERGY CORRECTION
      DMAT(NVWS,I)=DMAT(NVWS,I)-QLOSS*BSMS*HU*1000.*DELZ(I)/HREAK
	IF(I.LE.NZFR) THEN
      DMAT(NVWS,I)=DMAT(NVWS,I)+QH_CRCT*DELZ(I)/HNZFR
	ENDIF
	IF(KCHECK.EQ.1) THEN
      DMAT(NVWS,I)=DMAT(NVWS,I)-RVTAR(I)*9.3D06*KCHECK
	ENDIF
C      DMAT(NVWS,I)=DMAT(NVWS,I)+QH_CRCT*DELZ(I)/Hreak
C ***************************************************************
C 得到BMAT函数矩阵各具体结果
      IF (K.GT.0) GOTO 70
      DO 71 J=1,NVWS
	   DALT(J)=DMAT(J,I)
 71   CONTINUE
 80   K=K+1
      IF (K.LE.NVE) THEN
	      FEMF(K,I)=FEMF(K,I)+0.0001
		GOTO 53
	ELSEIF(K.EQ.NSGP) THEN
	WE(I)=WE(I)+0.0001
		GOTO 53
	ELSEIF(K.EQ.NSGP1) THEN
	X(I)=X(I)+0.0001
		GOTO 53
	ELSEIF(K.EQ.NVWS) THEN
	T(I)=T(I)+0.0001
		GOTO 53
	ENDIF

801	K=K+1
	KK=K-NVWS
      IF (KK.LE.NVE) THEN
	      FEMF(KK,I-1)=FEMF(KK,I-1)+0.0001
		GOTO 53
	ELSEIF(KK.EQ.NSGP) THEN
	WE(I-1)=WE(I-1)+0.0001
		GOTO 53
	ELSEIF(KK.EQ.NSGP1) THEN
	X(I-1)=X(I-1)+0.0001
		GOTO 53
	ELSEIF(KK.EQ.NVWS) THEN
	T(I-1)=T(I-1)+0.0001
		GOTO 53
	ENDIF

 70   KK=K-NVWS
	IF(KK.LE.0) THEN
 		IF (K.LE.NVE) THEN
			FEMF(K,I)=FEMF(K,I)-0.0001
		ELSEIF(K.EQ.NSGP) THEN
			WE(I)=WE(I)-0.0001
		ELSEIF(K.EQ.NSGP1) THEN
			X(I)=X(I)-0.0001
		ELSEIF(K.EQ.NVWS) THEN
			T(I)=T(I)-0.0001
		ENDIF
	ELSE
	IF(KK.LE.NVE) THEN
	      FEMF(KK,I-1)=FEMF(KK,I-1)-0.0001
	ELSEIF(KK.EQ.NSGP) THEN
	WE(I-1)=WE(I-1)-0.0001
	ELSEIF(KK.EQ.NSGP1) THEN
	X(I-1)=X(I-1)-0.0001
	ELSEIF(KK.EQ.NVWS) THEN
	T(I-1)=T(I-1)-0.0001
	ENDIF
	ENDIF
C #########################################################################
C 1-9个方程对第1到9个变量的导数
	IF(KK.LE.0) THEN
      DO 72 J=1,NVWS
         BMAT(J,K,I)=(DMAT(J,I)-DALT(J))/0.0001
C         IF (J.EQ.K.AND.BMAT(J,K,I).EQ.0.) BMAT(J,K,I)=1.0
C 对导数矩阵的一些特殊位置(第1-10个对角)的元素赋值
 72     CONTINUE
	ELSE
      DO 721 J=1,NVWS
         AMAT(J,KK,I-1)=(DMAT(J,I)-DALT(J))/0.0001
C         IF (J.EQ.K.AND.BMAT(J,K,I).EQ.0.) BMAT(J,K,I)=1.0
C 对导数矩阵的一些特殊位置(第1-10个对角)的元素赋值
 721     CONTINUE
	ENDIF

      IF (K.LE.NSGP1) GOTO 80
C	LIZHENG, PENG ZEFEI TEST: AUTO AMAT CALCULATION
	IF(K.LE.2*NVWS-1) GOTO 801
CCCCCCCCCCCCCCCCCCCCCCC	
      DO 81 J=1,NVWS       !将上面的变化还原.
	   DMAT(J,I)=DALT(J)
 81   CONTINUE
	GOTO 1993
C #########################################################################
C ***************************************************************
C 得到AMAT,CMAT函数矩阵各具体结果
C---  AMAT=0.
	IF (I.EQ.NZRA)  GOTO 16
	DO 14 J=1,NVE
        AMAT(J,J,I-1)=1.0
 14   CONTINUE
C	  DMAT(9,I)=DMAT(9,I)+WE(I-1)*X(I-1)
	  AMAT(NSGP,NSGP,I-1)=1.0
	  AMAT(NSGP,NSGP1,I-1)=0.0
	  AMAT(NSGP1,NSGP,I-1)=X(I-1)
	  AMAT(NSGP1,NSGP1,I-1)=WE(I-1)
C	ALL CMAT(1-9,1-10,I)=0.0  LIZHENG, WANG T.J. 2000/1/8 
16    CONTINUE

C=======================================
      IF (I.EQ.NZRA) GOTO 38
      DO 1051 K=1,NVE
         AMAT(NVWS,K,I-1)=HENTH(K,I-1)
 1051 CONTINUE
      AMAT(NVWS,NSGP,I-1)=
     &				(X(I-1)*HENTH(9,I-1)+(1.0-X(I-1))*HENTH(10,I-1))
      AMAT(NVWS,NSGP1,I-1)=WE(I-1)*(HENTH(9,I-1)-HENTH(10,I-1))
      AMAT(NVWS,NVWS,I-1)=(FEMF(1,I-1)*DHDT(1,I-1)
     &                    +FEMF(2,I-1)*DHDT(2,I-1)
     &                    +FEMF(3,I-1)*DHDT(3,I-1)
     &                    +FEMF(4,I-1)*DHDT(4,I-1)
     &                    +FEMF(5,I-1)*DHDT(5,I-1)
     &                    +FEMF(6,I-1)*DHDT(6,I-1)
     &                    +FEMF(7,I-1)*DHDT(7,I-1)
     &                    +FEMF(8,I-1)*DHDT(8,I-1))
	AMAT(NVWS,NVWS,I-1)=AMAT(NVWS,NVWS,I-1)
     &	+WE(I-1)*(X(I-1)*DHDT(9,I-1)+(1.0-X(I-1))*DHDT(10,I-1))
38	CONTINUE
	ENDIF
1993	CONTINUE
      DO 1990 J=1,NVWS
	   DMAT(J,I)=-DMAT(J,I)
 1990	CONTINUE
	SUM_RI=SUM_RI+RRI
 1991 CONTINUE

      RETURN
      END

C ############################################################
C 用于计算气化炉的各函数与导数的子程序
C ############################################################
C 考虑的反应如下:
C    考虑化学反应动力学的反应
C    --------------------------
C    气固两相反应
C      C + H2O -> CO + H2 	A1
C      C + 2H2 -> CH4 		A2
C      C + O2 -> CO + CO2 	A3
C      C + CO2 -> 2CO			A4
C    均相反应   
C      CO + 0.5O2 -> CO2		XK1
C      H2 + 0.5O2 -> H2O		XK2
C	 CO + H2O -> CO2 + H2	XK3
C	 CO2 + H2 -> CO + H2O	XK4
C	 CH4 + H2O -> CO + 3H2(考虑了可逆因素!!!)  XK5
C    --------------------------
C    不考虑化学反应动力学的反应
C    ==========================
C      V + O2 -> CO2 + H2O
C ############################################################