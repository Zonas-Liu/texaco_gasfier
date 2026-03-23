C ############################################################
C 用于进行初始化的子程序
C 与床的结构和几何尺寸相关!!!
C ############################################################
C---- FILE NAME INPUT.F

      SUBROUTINE EINGAB
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      INCLUDE 'COMMON.00'
      INCLUDE 'COMMON.01'
      INCLUDE 'COMMON.02'
      INCLUDE 'COMMON.03'
	DATA XMOL/32.,16.,28.,44.,34.,2.,28.,18.,12.,60./
	DATA XMTAR /12.913/


	KCHECK=0
	KTRLT=1
	KTRLR=1
	NZWS=30
	NZEL1=1
	NZEL2=30
	NZRE=30
C**************!用于Texaco气化炉结构**************************************
	NZR1=29	
	NZR2=27	
	NZR3=25	
	NZR4=23	
	NZR5=16	
	NZR6=9	
	NZR7=5	
C*********************************************************************


C**************!用于清华大学单段式气化炉实验台结构***********************
C	NZR1=29
C	NZR2=27
C	NZR3=25
C	NZR4=23
C	NZR5=16	
C	NZR6=9
C	NZR7=5
C*********************************************************************

C*************!用于清华大学颈缩式气化炉实验台结构**********************
c 	NZR1=29
c	NZR2=27
c	NZR3=20
c	NZR4=16
c	NZR5=14
c	NZR6=12
c	NZR7=5	
C*********************************************************************

C*************!用于清华大学渐扩式气化炉实验台结构**********************
C	NZR1=29
C	NZR2=27
C	NZR3=20
C	NZR4=16
C	NZR5=14
C	NZR6=12
C	NZR7=5	
C*********************************************************************

	N2FED=7
	NZRA=1
	NPRIX=1
	NZFED0=1

	KTRL_XK1=1
	KTRL_XK2=1
	KTRL_XK3=3
	KTRL_XK4=1
	KTRL_XK5=3
	CTRL_A1=0.28
	CTRL_A2=1.0
	CTRL_A3=1.0
	CTRL_A4=0.23
	CTRL_A5=1.0
	COEF_A1=0.1
	COEF_A2=0.1
	COEF_A3=0.1
	COEF_A4=0.1
	RO_SLURRY=1260.0
	ROS0=1260.0
	QH_CRCT=0.0

      OPEN (UNIT=7,FILE='DATAIN0.DAT',STATUS='OLD')
	READ(7,*) KTRL
	READ(7,*) ITMAX,SKONFE,SKONWE,SKONX,SKONT
      READ(7,*) BSLURRY,RATIO_COAL
	READ(7,*) FOXY,PURE_O2,OX_PART,RATIO_CO2
	READ(7,*) PFEED_SL,TFEED_SL,PFEED_OX,TFEED_OX
	READ(7,*) PFEED_CO2,TFEED_CO2
	READ(7,*) DP
	READ(7,*) HU,XVM
	READ(7,*) ELC,ELH,ELO,ELN,ELS,ELAS,ELH2O
	READ(7,*) TU,TW,PWK
	READ(7,*) QLOSS
C *** CCH: COEFFICIENTS USED TO CALCULATE THE REACTION RATE OF CARBON
C          COMBUSTION AND CO2 DEOXIDE
C *** NPRIX: THE NUMBER OF CELLS WITH SET-FREE OF VOLATILE

	WRITE(*,*) 'END OF INPUT  DATA!!'
	CLOSE(UNIT=7)

C	RATIO_CO2=1-OX_PART
C---------------------------------------------------------------
C	EVALUATION OF STRUCTURE PARAMETER
C---------------------------------------------------------------
C	ROS=2400.0
	NVE=NGAS
	NSGP=NVE+1
	NSGP1=NSGP+1
C 碳的质量平衡
	IF(KTRLT.EQ.1) THEN
	NVAR=NSGP1+1
	ELSE
	NVAR=NSGP1
	ENDIF
C 气体能量方程
C *** NVAR : THE NUMBER OF EQUATIONS 
C *** NPRIX: THE NUMBER OF CELLS WITH SET-FREE OF VOLATILE
C *** NZFR : THE TOP CELL WITH VOLATILE SET-FREE 
	NVWS=NVAR
      NZFR=NPRIX-NZRA+1
	NZFED=NZFED0-NZRA+1
C======================
	CALL GEOMETRY
C	HNZFR=HREAK-H(NZFR+1)
C	HFED=HREAK-H(NZFED+1)
C======================
C	MASS RATIO
	BSMS=BSLURRY*RATIO_COAL		!加入的煤的质量流率，kg/s
      BSWAF=BSMS*(1.-ELH2O-ELAS)		!加入的无水无灰基的煤的质量流量，kg/s
	FOX=FOXY*BSWAF/32./PURE_O2*22.4		!加入的氧气体积流量，Nm3/s
	GFOX=FOX*(PURE_O2*32.+(1-PURE_O2)*28.0)/22.4	! 加入的氧气质量流量，kg/s
	FCO2=FOX*RATIO_CO2	!加入的CO2的体积流量，Nm3/s
	GFCO2=FCO2/22.4*44		!加入的CO2的质量流量，kg/s
CCCCCCCCCCCCCCCCCCCCCCCCCCCC
C 计算各种气体的摩尔成份 
      DO 700 I=NZRA,NZFED
	WFA(I)=ELAS*BSMS*DELZ(I)/HFED
	WFC(I)=ELC*BSMS*DELZ(I)/HFED
	FEEDO2(I)=FOX*PURE_O2/22.4*DELZ(I)/HFED*OX_PART
	FEEDN2(I)=FOX*(1.0-PURE_O2)/22.4*DELZ(I)/HFED
	FEDCO2(I)=FOX*RATIO_CO2/22.4*DELZ(I)/HFED
700	FEDH2O(I)=(BSLURRY*(1.0-RATIO_COAL)+ELH2O*BSMS)/18.0*DELZ(I)/HFED
	FEEDO2(N2FED)=FOX*PURE_O2/22.4*DELZ(N2FED)/(H(N2FED)-H(N2FED+1))
     &				*(1-OX_PART)
	CALL FLUCHT
	CALL QHCRCT

CCCCCCCCCCCCCCCCCCCCCCCCCCCC
C	INITIALIZING OF UNKNOWN VARIABLES
	IF(KTRL.EQ.0) THEN
	OPEN(4,FILE='START.DAT',STATUS='UNKNOWN')
	READ(4,*)((FEMF(II,I),II=1,4),I=NZEL1,NZEL2)
	READ(4,*)((FEMF(II,I),II=5,8),I=NZEL1,NZEL2)
	READ(4,*)(T(I),I=NZEL1,NZEL2)
	READ(4,*)(X(I),I=NZEL1,NZEL2)
	READ(4,*)(WE(I),I=NZEL1,NZEL2)
	CLOSE(4)
	GOTO 1000

	ELSEIF(KCHECK.EQ.1) THEN
      DO 16 I=NZRA,NZRE
      FEMF(1,I)=FEEDO2(1)
     &		 +RO2(1)
      FEMF(2,I)=0.0/1000.0*4.+KCHECK*RVCH4(1)
      FEMF(3,I)=0.0/1000.0*4.+KCHECK*RCO(1)
      FEMF(4,I)=0.0/1000.0*4.+KCHECK*RCO2(1)
      FEMF(5,I)=0.0/1000.0*4.+KCHECK*RH2S(1)
      FEMF(6,I)=0.0/1000.0*4.+KCHECK*(RH2(1)+RVH2(1))
      FEMF(7,I)=GFOX*(1.0-PURE_O2)/28.0/NZFED
     &		 +KCHECK*REN2(1)
      FEMF(8,I)=(BSLURRY*(1.0-RATIO_COAL)+ELH2O*BSMS)/18.0/NZFED
     &		 +KCHECK*RVH2O(1)
      T(I)=298.15
      X(I)=WFC(1)/(WFA(1)+WFC(1))
C      X(I)=0.5
	WE(I)=WFA(1)+WFC(1)+RVTAR(1)*XMTAR
   16 CONTINUE
	GOTO 1000
      ELSE
	DO 15 I=NZRA,NZRE
      FEMF(1,I)=.555249E-02
C     &		 +FEEDO2(1)
C	&		 +RO2(1)
      FEMF(2,I)=.065000+KCHECK*RVCH4(1)
      FEMF(3,I)=.129528E+00/2.+KCHECK*RCO(1)
      FEMF(4,I)=.468267E-01+KCHECK*RCO2(1)
      FEMF(5,I)=.104452E-02+KCHECK*RH2S(1)
      FEMF(6,I)=.137525E-01*2.+KCHECK*(RH2(1)+RVH2(1))
      FEMF(7,I)=GFOX*(1.0-PURE_O2)/28.0/NZFED
     &		 +KCHECK*REN2(1)
      FEMF(8,I)=(BSLURRY*(1.0-RATIO_COAL)+ELH2O*BSMS)/18.0/NZFED
     &		 +KCHECK*RVH2O(1)
      T(I)=1500.0
C      X(I)=ELC/(ELC+ELAS)
      X(I)=.0665412E+00
	WE(I)=.5217118
C	&	  +BSMS*ELAS
   15 CONTINUE
	ENDIF
1000	CONTINUE
CCCCCCCCCCCCCCCCCCCC
C	ENERGY CORRECTION
C	IF(KCHECK.EQ.1) CALL  HCRCT
CCCCCCCCCCCCCCCCCCCC
c	GOTO 2000
CCCCCCCCCCCCCCCCCCCCCCCCCCCC

C	WRITE(1,155)
C  155 FORMAT(/,70('#'),/,'一、输入数据'//,4X,
C     &  '1.德士古气化炉几何尺寸')
C	WRITE(1,156)HREAK,DIA3
C  156 FORMAT(6X,'德士古气化炉高度:       ',F12.5,' M',/,
C     & 6X,'德士古气化炉半径:       ',F12.5,' M',/)

C      WRITE(1,166) NZRE-NZRA+1
C  166 FORMAT(4X,'2.小室划分情况',/,
C     &       6X,'德士古气化炉小室数目:   ',I8)
C	WRITE(1,181)
C  181	FORMAT(1X,5X,'小室划分',/,
C     &		6X,'I',5X,'小室高度',4X,'绝对高度',5X,'截面积')
C	DO 183 I=NZRA,NZRE
C	WRITE(1,182)I,DELZ(I),H(I),AT(I)
C183	CONTINUE
C182	FORMAT(1X,4X,I2,4X,3(F7.4,5X))
      
C      WRITE(1,159) 
C  159	FORMAT(/,4X,'3.给煤元素分析')
C      WRITE(1,160) ELC*100.,ELH*100.,ELO*100.0,
C     &   ELN*100.0,ELS*100.0,ELAS*100.0,ELH2O*100.0,XVM*100.0,HU
C 160 FORMAT(
C     &       6X,'碳的质量百分含量:		',F15.6,'%',/,
C     &       6X,'氢的质量百分含量:		',F15.6,'%',/,
C     &       6X,'氧的质量百分含量:		',F15.6,'%',/,
C     &       6X,'氮的质量百分含量:		',F15.6,'%',/,
C     &       6X,'硫的质量百分含量:		',F15.6,'%',/,
C     &       6X,'灰的质量百分含量:		',F15.6,'%',/,
C     &       6X,'水的质量百分含量:		',F15.6,'%',/,
C     &       6X,'挥发份的质量百分含量: ',F15.6,'%',/,
C     &       6X,'煤的热值:			',F15.6,' J/KG')
	WRITE(1,210)
210	FORMAT(/,4X,'4.运行条件')

C	WRITE(1,220)BSLURRY,RATIO_COAL*100.,BSMS,BSWAF,FOXY,FOX,GFOX,
C     &			PURE_O2*100.,OX_PART,RATIO_CO2,FCO2,N2FED,GFCO2
	WRITE(1,220)RATIO_COAL*100.,BSMS,FOXY,FOX,OX_PART,RATIO_CO2,N2FED
220	FORMAT(
C    &		6X,'水煤浆量:             ',F15.6,' KG/S',/,
     &       6X,'水煤浆浓度:           ',F15.6,' %',/,
     &	   6X,'给煤量:               ',F15.6,' KG/S',/,
C     &	   6X,'干燥无灰基质量:       ',F15.6,' KG/S',/,
     &	   6X,'氧煤比:               ',F15.6,' KG O2/KG BSWAF',/,
     &	   6X,'氧气体积流量:         ',F15.6,' NM3/S',/,
C     &	   6X,'氧气质量流量:         ',F15.6,' KG/S',/,
C     &	   6X,'氧气纯度:             ',F15.6,' %',/,
     &	   6X,'一段氧气比例：        ',F15.6,/,
     &	   6X,'加入CO2比例：         ',	F15.6,/,
C     &	   6X,'CO2体积流量：         ',	F15.6,/, 
     &	   6X,'二次氧气加入小室号：  ',	I2) 
C     &	   6X,'CO2质量流量：         ',	F15.6)			

c      WRITE(1,165) TU,PWK/1.0E5,PFEED_OX/1.0E5,TFEED_OX,PFEED_SL/1.0E5,
c     &			 TFEED_SL
c      WRITE(1,165) PWK/1.0E5
c165	FORMAT(
c     &		6X,'环境温度:             ',F15.6,' K ',/,
c     &       6X,'系统压力:             ',F15.6,' BAR')
c     &       6X,'给氧压力:             ',F15.6,' BAR',/,
c     &       6X,'给氧温度:             ',F15.6,' K',/,
c     &       6X,'给水煤浆压力:         ',F15.6,' BAR',/,
c     &       6X,'给水煤浆温度:         ',F15.6,' K',/)
c	WRITE(1,111)
c111	FORMAT(1X,/,5X,'挥发分',/,
c     &		2X,'I',5X,'RVCH4',4X,'RCO',6X,'RCO2',4X,'RVH20', 5X,
c     &        'RVH2',4X,'RVTAR',5X,'RH2S',5X,'REN2',5X,'RO2',6X,'RH2')
c	DO 113 I=NZRA,NZFR
c	WRITE(1,112)I,RVCH4(I),RCO(I),RCO2(I),RVH2O(I),RVH2(I),
c     &		      RVTAR(I),RH2S(I),REN2(I),RO2(I),RH2(I)
c113	CONTINUE
c112	FORMAT(1X,I2,10(2X,F7.4))
c	WRITE(1,230)XCVM0*100.,XC0*100.
c230	FORMAT(6X,'脱挥发份后转化率:     ',F15.6,' %',/,
c     &       6X,'脱挥发份后含碳量:     ',F15.6,' %')

c	WRITE(*,1900)
c 1900 FORMAT(1X,/)
c2000	CONTINUE
      WRITE(*,*)'???????????????  END OF S21.F  ???????????????'
	RETURN
	END


C ############################################################
C 用于计算德士古气化炉几何尺寸的子程序
C 与德士古气化炉的结构和几何尺寸相关!!!
C ############################################################
C !=====    GEOMETRY OF HARBIN PFBC 60 T/H     =====
      SUBROUTINE GEOMETRY
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      INCLUDE 'COMMON.00'
      INCLUDE 'COMMON.01'
C--------------------------------------------------------------------
C ___________      _______            ________________________     
C  DIAMETER1       |     |   NZRA=1             | 
C      |          |       |                     | 
C      |         |         |                 HREAK1=1.385M/8=0.173
C _____|_____   |___________|___      __________|_____________
C      |        |           | NZR1=9            |      
C      |        |           |              HREAK2=0.967M/5=0.193        
C      |        |___________|         __________|_____________       
C      |        |           | NZRW=14           |       
C  DIAMETER2    |           |              	  |
C      |        |           |                   |       
C      |        |           |              HREAK3=2.352M/12=0.196
C      |        |           |                   |       
C      |        |           |                   |       
C      |        |___________| NZRAE=25__________|_____________       
C      |        |           |                   |       
C      |        |           |              HREAK4=0.558M/2=0.196
C _____|_____   |___________|         __________|_____________
C      |          |       |   NZR2=28           |
C  DIAMETER3      |       |                HREAK5=0.50M/2=0.25
C _____|_____     |_______|           __________|_____________
C	 |			  |	  |		NZR3=30	   		  |
C  DIAMETER4        |   |                  HREAK6=0.50M/2=0.25
C _____|_____		  |___|		        __________|_____________
C	 |			   | |		NZR4=32     	  |
C  DIAMETER5         | |                   HREAK7=0.61M/2=0.305
C _____|_____		   |_|		NZRE=33 __________|_____________
C--------------------------------------------------------------------


C*****************Texaco气化炉结构*********************************      
	HREAK1=0.4
	HREAK2=0.4
	HREAK3=0.1926
	HREAK4=0.1926
	HREAK5=3.4
	HREAK6=3.4
	HREAK7=0.1876
	HREAK8=0.1876
	HREAK=HREAK1+HREAK2+HREAK3+HREAK4+HREAK5+HREAK6+HREAK7+HREAK8

	DIA1=1.005
	DIA2=0.935
	DIA3=1.175
	DIA4=1.725
	DIA5=2.0
	DIA6=2.0
	DIA7=1.675
	DIA8=1.025
C********************************************************************

C*****************Texaco颈缩式气化炉结构*********************************      
c	HREAK=9.055
c	HREAK1=0.25
c	HREAK2=0.838
c	HREAK3=4.445
c	HREAK4=1.258
c	HREAK5=0.083
c	HREAK6=0.279
c	HREAK7=1.482
c	HREAK8=0.419
c
c	DIA1=0.508
c	DIA2=1.092
c	DIA3=1.676
c	DIA4=0.98
c	DIA5=0.339
c	DIA6=0.728
c	DIA7=1.117
c	DIA8=0.653
C********************************************************************

C*****************Texaco渐扩式气化炉结构*********************************      
C	HREAK=9.055
C	HREAK1=0.25
C	HREAK2=0.838
C	HREAK3=4.445
C	HREAK4=1.258
C	HREAK5=0.083
C	HREAK6=0.279
C	HREAK7=1.482
C	HREAK8=0.419
C
C	DIA1=0.508
C	DIA2=1.092
C	DIA3=1.676
C	DIA4=0.98
C	DIA5=1.117
C	DIA6=1.117
C	DIA7=1.117
C	DIA8=0.653
C********************************************************************


C*****************清华大学单段式气化炉实验台结构*********************************      
C	HREAK=1.82
C	HREAK1=0.105
C	HREAK2=0.105
C	HREAK3=0.05
C	HREAK4=0.05
C	HREAK5=0.6675
C	HREAK6=0.6675
C	HREAK7=0.0875
C	HREAK8=0.0875
C
C	DIA1=0.15
C	DIA2=0.15
C	DIA3=0.25
C	DIA4=0.25
C	DIA5=0.35
C	DIA6=0.35
C	DIA7=0.205
C	DIA8=0.205
C********************************************************************

C*************用于清华大学颈缩式气化炉实验台结构**********************
C	HREAK=2.3546
C	HREAK1=0.21
C	HREAK2=0.1
C	HREAK3=1.335
C	HREAK4=0.175
C	HREAK5=0.0346
C	HREAK6=0.06
C	HREAK7=0.34
C	HREAK8=0.1
C
C	DIA1=0.15
C	DIA2=0.25
C	DIA3=0.35
C	DIA4=0.20475
C	DIA5=0.08
C	DIA6=0.14
C	DIA7=0.20
C	DIA8=0.117
C********************************************************************

C*************用于清华大学渐扩式气化炉实验台结构**********************
C	HREAK=2.3546
C	HREAK1=0.21
C	HREAK2=0.1
C	HREAK3=1.335
C	HREAK4=0.175
C	HREAK5=0.0346
C	HREAK6=0.06
C	HREAK7=0.34
C	HREAK8=0.1
C
C	DIA1=0.15
C	DIA2=0.25
C	DIA3=0.35
C	DIA4=0.20475
C	DIA5=0.20
C	DIA6=0.20
C	DIA7=0.20
C	DIA8=0.117
C********************************************************************



      DO 9970 I=NZEL1,NZEL2
      DELZ(I)=0.0
      H(I)=0.0
      AT(I)=0.0
	AR(I)=0.0
9970  CONTINUE
C     DELZ(I) STANDS FOR THE NET HEIGHT OF I CELL
C     H(I) STANDS FOR THE ELEVATION OF I CELL
C     AT(I) STANDS FOR THE CROSS SECTION
C *********************************************************************
C 以下为出口段的小室划分情况
      DO 9982 I=NZRE,NZR1,-1
      DELZ(I)=HREAK1/(NZRE-NZR1+1)
      H(I)=DELZ(I)*(NZRE-I+1)
      AT(I)=DIA1*DIA1*PI/4.0
	AR(I)=DIA1*PI
9982  CONTINUE
C *********************************************************************

C *********************************************************************
C 以下为下部锥段的小室划分情况
      DO 9983 I=NZR1-1,NZR2,-1
      DELZ(I)=HREAK2/(NZR1-NZR2)
      H(I)=HREAK1+DELZ(I)*(NZR1-I)
	AT(I)=DIA2*DIA2*PI/4.0
	AR(I)=DIA2*PI
9983  CONTINUE
C *********************************************************************

C *********************************************************************
C   以下为主流段小室划分情况
C =====================================================================
      DO 9984 I=NZR2-1,NZR3,-1
      DELZ(I)=HREAK3/(NZR2-NZR3)
	H(I)=HREAK1+HREAK2+DELZ(I)*(NZR2-I)
      AT(I)=DIA3*DIA3*PI/4.0
	AR(I)=DIA3*PI
9984  CONTINUE
C *********************************************************************
C   以下为主流段小室划分情况
C =====================================================================
      DO 9985 I=NZR3-1,NZR4,-1
      DELZ(I)=HREAK4/(NZR3-NZR4)
	H(I)=HREAK1+HREAK2+HREAK3+DELZ(I)*(NZR3-I)
      AT(I)=DIA4*DIA4*PI/4.0
	AR(I)=DIA4*PI
9985  CONTINUE
C *********************************************************************
C   以下为主流段小室划分情况
C =====================================================================
      DO 9986 I=NZR4-1,NZR5,-1
      DELZ(I)=HREAK5/(NZR4-NZR5)
	H(I)=HREAK1+HREAK2+HREAK3+HREAK4+DELZ(I)*(NZR4-I)
      AT(I)=DIA5*DIA5*PI/4.0
	AR(I)=DIA5*PI
9986  CONTINUE
C *********************************************************************
C   以下为主流段小室划分情况
C =====================================================================
      DO 9987 I=NZR5-1,NZR6,-1
      DELZ(I)=HREAK6/(NZR5-NZR6)
	H(I)=HREAK1+HREAK2+HREAK3+HREAK4+HREAK5+DELZ(I)*(NZR5-I)
      AT(I)=DIA6*DIA6*PI/4.0
	AR(I)=DIA6*PI
9987  CONTINUE
C *********************************************************************
C   以下为主流段小室划分情况
C =====================================================================
      DO 9988 I=NZR6-1,NZR7,-1
      DELZ(I)=HREAK7/(NZR6-NZR7)
	H(I)=HREAK1+HREAK2+HREAK3+HREAK4+HREAK5+HREAK6+DELZ(I)*(NZR6-I)
      AT(I)=DIA7*DIA7*PI/4.0
	AR(I)=DIA7*PI
9988  CONTINUE

C *********************************************************************
C 以下为进口段的小室划分情况
      DO 9989 I=NZR7-1,NZRA,-1
      DELZ(I)=HREAK8/(NZR7-NZRA)
      H(I)=HREAK1+HREAK2+HREAK3+HREAK4+HREAK5+HREAK6+HREAK7
     &	+DELZ(I)*(NZR7-I)
      AT(I)=DIA8*DIA8*PI/4.0
	AR(I)=DIA8*PI
9989  CONTINUE

	HNZFR=0.0
	HFED=0.0
	DO 8000 I=NZRA,NZFR
8000	HNZFR=HNZFR+DELZ(I)
	DO 8100 I=NZRA,NZFED
8100	HFED=HFED+DELZ(I)
      RETURN
      END
C	************对煤的发热量进行修正子程序****************
      SUBROUTINE QHCRCT
	IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      INCLUDE 'COMMON.00'
      INCLUDE 'COMMON.01'
      INCLUDE 'COMMON.02'
      INCLUDE 'COMMON.03'

	RCO21=0.0
	RCO1=0.0
	RVCH41=0.0
	RVTAR1=0.0
	RH2S1=0.0
	RH2O1=0.0
	DO 100 I=NZRA,NZRE
	RCO21=RCO21+RCO2(I)
	RCO1=RCO1+RCO(I)
	RVCH41=RVCH41+RVCH4(I)
	RVTAR1=RVTAR1+RVTAR(I)
	RH2S1=RH2S1+RH2S(I)
	RH2O1=RH2O1+RVH2O(I)
100	CONTINUE

	HUU=((ELC/12.)*BSMS*(-393.6933)+
     &    (ELH/2.-ELS/32.)*BSMS*(-286.5)-
     &     RCO21*BSMS*(-393.6933)-
     &     RCO1*BSMS*(-110.59412)- 
     &	 RVCH41*BSMS*(-74.84568)-
     &     RVTAR1*BSMS*(-9.3))/BSMS*1000.-
     &	 RH2S1*(-20.18)
	QH_CRCT=(HUU+HU)*1000.

C	ENTHALLPY AFTER PYROLYSIS
	HF_H2O1=ENTHP(8,'L   ',298.15D0,PW)/1.0E6
	H_IN=(RVCH41*(-74.84568)+RCO1*(-110.59412)+RCO21*(-393.6933)
     &	   +RH2O1*HF_H2O1+RH2S1*(-20.18)+RVTAR1*(-9.3))
C	H_IN=H_IN*1000.

	CO2_OUT=ELC*BSMS/12.
	H2O_OUT=ELH*BSMS/2.-RH2S1

	H_PRDCT=CO2_OUT*(-393.6933)+H2O_OUT*HF_H2O1+RH2S1*(-20.18)
	
      DELTH=(H_PRDCT-H_IN)/BSMS
	
      H_RACT=HU/1000.

	RETURN
	END
