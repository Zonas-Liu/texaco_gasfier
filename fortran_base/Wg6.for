C*******************************************************
C 均相反应反应常数(Rk)
C XK1: CO+1/2 O2---CO2
C XK2: H2+1/2 O2---H2O
C XK3: CO +  H2O---CO2 + H2
C XK4: CO2 +  H2---CO + H2O
C XK5: CH4 + H20---CO + 3H2
C*******************************************************
C*******************************************************
C XK1: CO+1/2 O2---CO2 
C*******************************************************      
      FUNCTION XK1(I)
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      INCLUDE 'COMMON.00'
      INCLUDE 'COMMON.01'
      INCLUDE 'COMMON.02'      

	DO 778 J=1,NGAS
778	Y(J)=FEMF(J,I)/FEM(I)

	IF(Y(1).LT.1.0e-10.OR.Y(3).LT.1.0e-10) THEN
	XK1=0.0
	RETURN
	ENDIF

	XK10=3.09D8*DEXP(-9.976D7/(RAG*T(I)))*(PWK/(RAG*T(I)))**2
     &    *AT(I)*DELZ(I)
C	XK1=XK10*Y(1)*Y(3)*KTRL_XK1
	XK1=XK10*Y(1)*Y(3)*KTRL_XK1
c	XK1=0.0
C XKJ的单位M3/(KMOL.S)*(KMOL/M3)**2*M3=KMOL/S
C 体积反应速率,以后反应掉的物质量为XKJ*(FJ(1,I)/FJM(I))*(FJ(3,I)/FJM(I))
C ACCORDING TO CEN KEFA AND ZHAO LI

      RETURN
      END

C*******************************************************
C XK2: H2+1/2 O2---H2O 
C*******************************************************
      FUNCTION XK2(I)
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      INCLUDE 'COMMON.00'
      INCLUDE 'COMMON.01'
      INCLUDE 'COMMON.02'      

	DO 778 J=1,NGAS
778	Y(J)=FEMF(J,I)/FEM(I)

	IF(Y(1).LT.1.0e-10.OR.Y(6).LT.1.0e-10) THEN
	XK2=0.0
	RETURN
	ENDIF
	XK20=8.83D8*DEXP(-9.976D7/(RAG*T(I)))
     &    *AT(I)*DELZ(I)*(PWK/(RAG*T(I)))**2
C	&    *AT(I)*DELZ(I)*(PWK/(RAG*T(I)))**2
C	XK2=XK20*Y(1)*Y(6)*KTRL_XK2
	XK2=XK20*Y(1)*Y(6)*KTRL_XK2
c	XK2=0.0
C 体积反应速率,以后反应掉的物质量为XHJ*(FJ(6,I)/FJM(I))**2*(FJ(1,I)/FJM(I))
C ACCORDING TO ZHAO LI AND CEN KEFA !! CEN KEFA IS 2.0 ZHAOLI IS 3.0
      RETURN
      END

C*******************************************************
C XK3: CO+H2O-->CO2+H2
C*******************************************************
      FUNCTION XK3(I)
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      INCLUDE 'COMMON.00'
      INCLUDE 'COMMON.01'
      INCLUDE 'COMMON.02'      

C	PO2=FEMF(1,I)/FEM(I)
C	IF(PO2.GE.0.0) THEN
C	XK3=0.0
C	RETURN
C	ENDIF
	DO 778 J=1,NGAS
778	Y(J)=FEMF(J,I)/FEM(I)

	IF(Y(3).LT.0.000.OR.Y(8).LT.0.000) THEN
	XK3=0.0
	RETURN
	ENDIF

	XK30=2.978D12*DEXP(-3.69D8/(RAG*T(I)))
     &      *AT(I)*DELZ(I)*(PWK/(RAG*T(I)))**2
C	XK3=XK30*Y(3)*Y(8)*KTRL_XK3
	XK3=XK30*Y(3)*Y(8)*KTRL_XK3
C	XK3=0.0
C 体积反应速率,以后反应掉的物质量为XSH1J*(FJ(3,I)/FJM(I))*(FJ(8,I)/FJM(I))
C ACCORDING TO CEN KEFA AND ZHAO LI
      RETURN
      END

C*******************************************************
C XK4:CO2+H2-->CO+H2O
C*******************************************************
      FUNCTION XK4(I)
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      INCLUDE 'COMMON.00'
      INCLUDE 'COMMON.01'
      INCLUDE 'COMMON.02'      

	DO 778 J=1,NGAS
778	Y(J)=FEMF(J,I)/FEM(I)

	XK40=0.215*6.245D14*DEXP(-3.983D8/(RAG*T(I)))
     &      *AT(I)*DELZ(I)*(PWK/(RAG*T(I)))**2
	XK4=XK40*Y(4)*Y(6)*KTRL_XK4
C	XK4=XK40*Y(4)*Y(6)*KTRL_XK4*0.8		!20080327
C 体积反应速率,以后反应掉的物质量为XSH2J*(FJ(4,I)/FJM(I))*(FJ(6,I)/FJM(I))
C ACCORDING TO CEN KEFA 6.245D14 BUT ZHAO LI IS 7.145D14

      RETURN
      END

C*******************************************************
C XK5: CH4+H20-->CO+3H2
C*******************************************************
      FUNCTION XK5(I)
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      INCLUDE 'COMMON.00'
      INCLUDE 'COMMON.01'
      INCLUDE 'COMMON.02'      

	DO 778 J=1,NGAS
778	Y(J)=FEMF(J,I)/FEM(I)

	IF(Y(2).LT.1.0e-10) THEN
	XK5=0.0*KTRL_XK5
	RETURN
	ENDIF

	XK50=312.0*DEXP(-3.0D4/(1.987*T(I)))
     &       *AT(I)*DELZ(I)*(PWK/(RAG*T(I)))
C	XK5=XK50*Y(2)*KTRL_XK5
	XK5=XK50*Y(2)*KTRL_XK5
	 
C	XK5=0.0
C 体积反应速率,以后反应掉的物质量为XK5*(FJ(9,I)/FJM(I))
C ACCORDING TO WEN
 
      RETURN
      END
C*******************************************************
C XK6: CH4+2 O2---CO2+2H2O 
C*******************************************************      
      FUNCTION XK6(I)
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      INCLUDE 'COMMON.00'
      INCLUDE 'COMMON.01'
      INCLUDE 'COMMON.02'      

	DO 778 J=1,NGAS
778	Y(J)=FEMF(J,I)/FEM(I)

	IF(Y(1).LT.0.0001.OR.Y(2).LT.0.0001) THEN
	XK6=0.0
	RETURN
	ENDIF

	XK60=3.552D14*DEXP(-9.304D8/(RAG*T(I)))*(PWK/(RAG*T(I)))**2
     &    *AT(I)*DELZ(I)
	XK6=XK60*Y(1)*Y(2)
c	XK6=0.0
C XKJ的单位M3/(KMOL.S)*(KMOL/M3)**2*M3=KMOL/S
C 体积反应速率,以后反应掉的物质量为XKJ*(FJ(1,I)/FJM(I))*(FJ(3,I)/FJM(I))
C ACCORDING TO CEN KEFA P320

      RETURN
      END
      SUBROUTINE FLUCHT
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      INCLUDE 'COMMON.00'
      INCLUDE 'COMMON.01'
      INCLUDE 'COMMON.02'

      XOCH4=2. 
C *** XOCH4代表1摩尔甲烷完全燃烧所需的氧气的摩尔数
      XOH2=0.5  
C *** XOH2代表1摩尔氢气完全燃烧所需的氧气的摩尔数      
      XOCO=0.5  
C *** XOCO代表1摩尔CO完全燃烧所需的氧气的摩尔数      
      XHOCH=2.
C *** XHOCH代表1摩尔甲烷完全燃烧所产生的H2O的摩尔数     
      XHOH2=1. 
C *** XHOH2代表1摩尔氢气完全燃烧所产生的H2O的摩尔数            
      XCOCH=1. 
C *** XCOCH代表1摩尔甲烷完全燃烧所产生的CO2的摩尔数
      XOTAR=1.16525
C *** XOTAR代表1摩尔焦油完全燃烧所需的氧气的摩尔数
      XCTAR_CO=1.0
C *** XCTAR_CO代表1摩尔焦油/CO完全燃烧所产生的CO2的摩尔数
	XHTAR=0.3445
C *** XHTAR代表1摩尔焦油完全燃烧所产生的H2O的摩尔数
	IF(KCHECK.EQ.1) THEN
      XOCO=0.  
      XHOCH=0.
      XHOH2=0. 
      XCOCH=0. 
      XOTAR=0. 
      XCTAR_CO=0.0 
	XHTAR=0.0
      XOCH4=0. 
      XOH2=0.
	ENDIF  
C      BSWAF=BSMS*(1.-ELH2O-ELAS)
          
C=    THE SORT OF SUBSTANCES CONSIDERED IN THE VOLATILE RELEASE: 10
C=    RCO2(I),RCO(I),RVH2(I),RVH2O(I),RVCH4(I),RVTAR(I),RH2(I),
C=    RO2(I),REN2(I),RH2S(I)

C *****************************************************************
C 初始化数组
      DO 1 I=NZEL1,NZEL2
      RCO2(I)=0. 
C *** RCO2(I)代表I小室中由煤中挥发份挥发分解得到的CO2的数量(摩尔数)      
      RCO(I)=0. 
C *** RCO(I)代表I小室中由煤中挥发份挥发分解得到的CO的数量(摩尔数)            
      RVH2(I)=0.
C *** RVH2(I)代表I小室中由煤中挥发份挥发分解得到的H2的数量(摩尔数)                   
      RVH2O(I)=0.
C *** RVH2O(I)代表I小室中由煤中挥发份挥发分解得到的H2O的数量(摩尔数)                   
      RVCH4(I)=0.
C *** RVCH4(I)代表I小室中由煤中挥发份挥发分解得到的CH4的数量(摩尔数)                   
      RVTAR(I)=0.
C *** RVTAR(I)代表I小室中由煤中挥发份挥发分解得到的TAR(焦油)的数量(摩尔数)                   

      RH2(I)=0.
C *** RH2(I)代表煤中氢元素除以挥发份中的H2,H2O,H2S,CH4和TAR形式释放外
C     其余均以氢气形式释放在I小室的数量(摩尔数)
      RO2(I)=0.
C *** RO2(I)代表煤中氧元素除以挥发份中的H2O,CO,CO2和TAR形式释放外
C     其余均以氧气形式释放在I小室的数量(摩尔数)

      REN2(I)=0.
C *** REN2代表煤中氮元素均以氮气的形式释放在I小室的数量(摩尔数)
    1 RH2S(I)=0.
C *** RH2S(I)代表煤中硫元素均以H2S形式释放在I小室的数量(摩尔数)
C *****************************************************************

   20 IF (XVM.GT.0.5166) XVM=0.5166
C *** XVM_TRUE代表煤中无水无灰基的挥发份的质量百分比
  
C===  FAK=(1.-ELH2O)-ELAS*(1.-ELH2O)
      FAK=1.0
      PRC=FAK*ELC         ! in kg/kg coal
C *** PRC代表1KG煤中所含的C元素质量
      PRN=FAK*ELN
C *** PRN代表1KG煤中所含的N元素质量
      PRS=FAK*ELS                  
C *** PRS代表1KG煤中所含的S元素质量      
      PRH=FAK*ELH                  
C *** PRH代表1KG煤中所含的H元素质量      
      PRO=FAK*ELO
C *** PRO代表1KG煤中所含的O元素质量
    
      RH2S_TOTAL=PRS*BSMS/32.0
C *** RH2S_TOTAL代表给煤中所有硫元素全部变为H2S所能产生的H2S的数量(摩尔数) 
	REN2_TOTAL=PRN*BSMS/28.0
C *** REN2_TOTAL代表给煤中所有氮元素全部变为N2所能产生的N2的数量(摩尔数) 
      RH2_TOTAL=PRH*BSMS/2.0                                                
C *** RH2_TOTAL代表给煤中所有氢元素全部变为H2所能产生的H2的数量(摩尔数)       
      RO2_TOTAL=PRO*BSMS/32.0
C *** RO2_TOTAL代表给煤中所有氧元素全部变为O2所能产生的O2的数量(摩尔数) 

      IF (XVM.EQ.0.) GOTO 902

C     CORRELATION FOR VOLATILE SETTING OFF      
      RVCH41=(0.201-0.469*XVM+0.261*XVM**2)
     &       *XVM*BSWAF/16.
C *** BSWAF代表给煤的干燥无灰基总质量流量
C *** RVCH41代表由煤中挥发份挥发分解得到的CH4的总数量(摩尔数)                   
      RVTAR1=(-0.325+7.279*XVM-12.88*XVM**2)
     &       *XVM*BSWAF/12.913
C *** RVTAR1代表由煤中挥发份挥发分解得到的TAR的总数量(摩尔数)                         
      RVH21=(0.157-0.868*XVM+1.388*XVM**2)
     &      *XVM*BSWAF/2.
C *** RVH21代表由煤中挥发份挥发分解得到的H2的总数量(摩尔数),
C     不含由其它多余氢元素转变而来的H2                   
      RCO21=(0.13-0.9*XVM+1.906*XVM**2)
     &      *XVM*BSWAF/44.
C *** RCO21代表由煤中挥发份挥发分解得到的CO2的总数量(摩尔数)                   
      RCO1=(0.428-2.653*XVM+4.845*XVM**2)
     &     *XVM*BSWAF/28.
C *** RCO1代表由煤中挥发份挥发分解得到的CO的总数量(摩尔数)                   
      RVH2O1=(0.409-2.389*XVM+4.5*XVM**2)
     &       *XVM*BSWAF/18.
C *** RVH2O1代表由煤中挥发份挥发分解得到的H2O的总数量(摩尔数)                   

C--------------------------------------------------------------      
C     RESIDUAL H & O ELEMENTS
      RH2_RE=RH2_TOTAL-2.*RVCH41-RVH21-RVH2O1-0.3445*RVTAR1-RH2S_TOTAL
C *** RH2_RE代表由煤中剩余氢元素转变为H2的总数量(摩尔数),      
      RO2_RE=RO2_TOTAL-RCO21-0.5*(RCO1+RVH2O1)-0.007*RVTAR1
C *** RO2_RE代表由煤中剩余氧元素转变为O2的总数量(摩尔数),           

C--------------------------------------------------------------     
C     FAK1:TOTAL OXYGEN NEEDED FOR DEVOLATILIZATION
C     FAK2:TOTAL HYDRYGEN FOR DEVOLATILIZATION

      FAK1=RCO21+0.5*RCO1+0.5*RVH2O1+0.007*RVTAR1
C *** FAK1代表煤中挥发份析出时所需氧气数量
      FAK2=RVH21+RVH2O1+2.*RVCH41+0.3445*RVTAR1
C *** FAK2代表煤中挥发份析出时所需氢气数量
      FAK3=RVH21+2.*RVCH41                
C *** FAK3代表煤中挥发份氢气和甲烷析出时所需氢气数量      
      FAK4=RCO21+0.5*RCO1                 
C *** FAK4代表煤中挥发份CO2和CO析出时所需氧气数量      

      IF(RH2_RE.GE.0.) GOTO 900        
C 代表煤中挥发份析出后氢元素有剩余时      

      IF(RO2_RE.GE.0.) GOTO 903             
C 代表煤中挥发份析出后氧元素有剩余时            

      GOTO 904
C     MEANS NOT ENOUGH O2, THEN OUTPUT DECREASE PROPOTIONALLY
C     MEANS NO LEFT O2
C     QUESTION: S IS NOT USED OUT!!! THINK ABOUT IT!

 900  IF (RO2_RE.GE.0.) GOTO 901
 
C ************************************************************
C 代表煤中挥发份析出后氢元素有剩余,而氧元素不足时      
      RVCH4K=RVCH41
      RVH2K=RVH21
C 其它含氧元素的挥发份按比例析出
      RVH2OK=RO2_TOTAL*RVH2O1/FAK1
      RCO2K=RO2_TOTAL*RCO21/FAK1
      RCOK=RO2_TOTAL*RCO1/FAK1
      RVTARK=RO2_TOTAL*RVTAR1/FAK1

      RH2S_TOTAL=RH2S_TOTAL
C 还认为硫元素完全以挥发份中H2S的形式析出!!!
	REN2_TOTAL=REN2_TOTAL
      
      GOTO 902 
C *************************************************************

C ************************************************************
C 代表煤中挥发份析出后氢元素不足,而氧元素有剩余时      
 903  RCOK=RCO1
      RCO2K=RCO21
      RVH2OK=(RH2_TOTAL-RH2S_TOTAL)*RVH2O1/FAK2
      RVH2K=(RH2_TOTAL-RH2S_TOTAL)*RVH21/FAK2
      RVCH4K=(RH2_TOTAL-RH2S_TOTAL)*RVCH41/FAK2
      RVTARK=(RH2_TOTAL-RH2S_TOTAL)*RVTAR1/FAK2
      GOTO 902                                               
C ************************************************************
      
C ************************************************************
C 代表煤中挥发份析出后氢氧元素均不足时      
 904  VH2OK1=(RH2_TOTAL-RH2S_TOTAL)*RVH2O1/FAK2
      VH2OK2=RO2_TOTAL*RVH2O1/FAK1
      VTARK1=(RH2_TOTAL-RH2S_TOTAL)*RVTAR1/FAK2
      VTARK2=RO2_TOTAL*RVTAR1/FAK1
      IF (VH2OK1.GE.VH2OK2.AND.VTARK1.GE.VTARK2) GOTO 905
      IF (VH2OK1.GE.VH2OK2.AND.VTARK1.LT.VTARK2) GOTO 906
      IF (VH2OK1.LT.VH2OK2.AND.VTARK1.GE.VTARK2) GOTO 907
      IF (VH2OK1.LT.VH2OK2.AND.VTARK1.LT.VTARK2) GOTO 908
      
 905  RVH2OK=VH2OK2
      RVTARK=VTARK2
      RCOK=RO2_TOTAL*RCO1/FAK1
      RCO2K=RO2_TOTAL*RCO21/FAK1
      RH2_RE=RH2_TOTAL-RH2S_TOTAL-RVH2OK-RVH21-2.*RVCH41-0.3445*RVTARK

      IF (RH2_RE.GE.0) GOTO 911

      RVH2K=(RH2_TOTAL-RH2S_TOTAL-RVH2OK-0.3445*RVTARK)*RVH21/FAK3
      RVCH4K=(RH2_TOTAL-RH2S_TOTAL-RVH2OK-0.3445*RVTARK)*RVCH41/FAK3
      GOTO 902

 911  RVH2K=RVH21
      RVCH4K=RVCH41
      GOTO 902

 906  RVH2OK=VH2OK2
      RVTARK=VTARK1
 999  RH2_RE=RH2_TOTAL-RH2S_TOTAL-RVH2OK-0.3445*RVTARK-2.*RVCH41-RVH21
      RO2_RE=RO2_TOTAL-0.5*RVH2OK-0.007*RVTARK-0.5*RCO1-RCO21

      IF (RH2_RE.GE.0)GOTO 912
      IF (RO2_RE.GE.0)GOTO 913
      GOTO 914

 912  IF (RO2_RE.GE.0)GOTO 915
      RVH2K=RVH21
      RVCH4K=RVCH41
      RCOK=(RO2_TOTAL-0.5*RVH2OK-0.007*RVTARK)*RCO1/FAK4
      RCO2K=(RO2_TOTAL-0.5*RVH2OK-0.007*RVTARK)*RCO21/FAK4
      GOTO 902

 913  RCOK=RCO1
      RCO2K=RCO21
      RVCH4K=(RH2_TOTAL-RH2S_TOTAL-RVH2OK-0.3445*RVTARK)*RVCH41/FAK3
      RVH2K=(RH2_TOTAL-RH2S_TOTAL-RVH2OK-0.3445*RVTARK)*RVH21/FAK3
      GOTO 902

 914  RCOK=(RO2_TOTAL-0.5*RVH2OK-0.007*RVTARK)*RCO1/FAK4
      RCO2K=(RO2_TOTAL-0.5*RVH2OK-0.007*RVTARK)*RCO21/FAK4
      RVCH4K=(RH2_TOTAL-RH2S_TOTAL-RVH2OK-0.3445*RVTARK)*RVCH41/FAK3
      RVH2K=(RH2_TOTAL-RH2S_TOTAL-RVH2OK-0.3445*RVTARK)*RVH21/FAK3
      GOTO 902

 915  RCOK=RCO1
      RCO2K=RCO21
      RVCH4K=RVCH41
      RVH2K=RVH21
      GOTO 902

 907  RVH2OK=VH2OK1
      RVTARK=VTARK1
      GOTO 999

 908  RVH2OK=VH2OK1
      RVTARK=VTARK2
      RVH2K=(RH2_TOTAL-RH2S_TOTAL)*RVH21/FAK2
      RVCH4K=(RH2_TOTAL-RH2S_TOTAL)*RVCH41/FAK2
      RO2_RE=RO2_TOTAL-0.5*RVH2OK-0.007*RVTARK-0.5*RCO1-RCO21

      IF (RO2_RE.GE.0.) GOTO 916
      RCOK=(RO2_TOTAL-0.5*RVH2OK-0.007*RVTARK)*RCO1/FAK4
      RCO2K=(RO2_TOTAL-0.5*RVH2OK-0.007*RVTARK)*RCO21/FAK4
      GOTO 902

 916  RCOK=RCO1
      RCO2K=RCO21
C ************************************************************

C ************************************************************
 902  RVCH41=RVCH4K
      RVH21=RVH2K

      RVH2O1=RVH2OK
      RCO1=RCOK
      RVTAR1=RVTARK
      RCO21=RCO2K

C *************************************************************
C 代表煤中挥发份析出后氢和氧元素均有剩余时
 901  RV1=RVCH41+RVH21+RCO1+RCO21+RVH2O1+RVTAR1
C *************************************************************

      DO 700 I=NZRA,NZFR
      RH2(I)=(PRH*BSMS/2.0-(2.*RVCH41+RVH21+RVH2O1+RH2S_TOTAL
     &       +0.3445*RVTAR1))*DELZ(I)/HNZFR
      RO2(I)=(PRO*BSMS/32.-(0.5*(RCO1+RVH2O1)+0.007
     &       *RVTAR1+RCO21))*DELZ(I)/HNZFR
      REN2(I)=PRN*BSMS/28.0*DELZ(I)/HNZFR
	RH2S(I)=PRS*BSMS/32.*DELZ(I)/HNZFR
  700 CONTINUE

	SUM_WFC=0.0
      DO 3331 I=NZRA,NZFED
	WFC(I)=(PRC*BSMS-12.*(RCO1+RCO21+RVCH41)-12.*RVTAR1)
     &      /(NZFED-NZRA+1)
	SUM_WFC=SUM_WFC+WFC(I)
3331  CONTINUE

      DO 2 I=NZRA,NZFR
      RVCH4(I)=RVCH41*DELZ(I)/HNZFR
      RVH2(I)=RVH21*DELZ(I)/HNZFR
      RVH2O(I)=RVH2O1*DELZ(I)/HNZFR
      RCO(I)=RCO1*DELZ(I)/HNZFR
      RCO2(I)=RCO21*DELZ(I)/HNZFR
 2    RVTAR(I)=RVTAR1*DELZ(I)/HNZFR
C	TOTAL CONVERSION
	VM0=0.0
	DO 3 I=NZRA,NZRE
	VM0=VM0+RVCH4(I)*16.+RVH2(I)*2.+RVH2O(I)*18.+RCO(I)*28.
     &	   +RCO2(I)*44.+RVTAR(I)*12.913
     &	   +RH2(I)*2.+RO2(I)*32.+REN2(I)*28.+RH2S(I)*34.
3	CONTINUE
C	CONVERSION RATE AFTER DEVOLATILIZATION
	XCVM0=VM0/BSWAF
C	CARBON CONTENT  AFTER DEVOLATILIZATION
	XC0=SUM_WFC/(SUM_WFC+BSMS*ELAS)
	GOTO 1000

C==========MASS BALANCE CHECK===============
C	ELEMENT:  CH4,CO,CO2,H2O,TAR,H2,O2,N2,H2,H2S
C	C: CH4,CO,CO2,TAR
C	H: CH4,H2O,H2,H2,TAR,H2S
C	O: CO,CO2,H2O,TAR,O2
C	N: N2
C	S: H2S
 	C_TOTAL=BSMS*ELC
	H_TOTAL=BSMS*ELH
 	O_TOTAL=BSMS*ELO
	XN_TOTAL=BSMS*ELN
 	S_TOTAL=BSMS*ELS

	SUM_C=0.0
	SUM_H=0.0
	SUM_O=0.0
	SUM_N=0.0
	SUM_S=0.0
C	SUM_WFC=0.0
	DO 100 I=NZRA,NZRE
	SUM_C=SUM_C+(RVCH4(I)+RCO(I)+RCO2(I)+RVTAR(I))*12.0+WFC(I)
	SUM_H=SUM_H+(RVCH4(I)*2.0+RVH2O(I)+RVH2(I)+RH2(I)
     &	+0.3445*RVTAR(I)+RH2S(I))*2.0
	SUM_O=SUM_O+(RCO(I)+RCO2(I)*2.0+RVH2O(I)
     &	+0.014*RVTAR(I)+RO2(I)*2.0)*16.0
	SUM_N=SUM_N+REN2(I)*28.0
	SUM_S=SUM_S+RH2S(I)*32.0
C	SUM_WFC=SUM_WFC+WFC(I)
100	CONTINUE
C	WRITE(1,110)C_TOTAL,SUM_C,C_TOTAL-SUM_C
C	WRITE(1,111)H_TOTAL,SUM_H,H_TOTAL-SUM_H
C	WRITE(1,112)O_TOTAL,SUM_O,O_TOTAL-SUM_O
C	WRITE(1,113)XN_TOTAL,SUM_N,XN_TOTAL-SUM_N
C	WRITE(1,114)S_TOTAL,SUM_S,S_TOTAL-SUM_S
110	FORMAT(1X,'CIN=',F7.4,2X,'COUT=',F7.4,2X,'DELTA=',F7.4)      
111	FORMAT(1X,'HIN=',F7.4,2X,'HOUT=',F7.4,2X,'DELTA=',F7.4)      
112	FORMAT(1X,'OIN=',F7.4,2X,'OOUT=',F7.4,2X,'DELTA=',F7.4)      
113	FORMAT(1X,'NIN=',F7.4,2X,'NOUT=',F7.4,2X,'DELTA=',F7.4)      
114	FORMAT(1X,'SIN=',F7.4,2X,'SOUT=',F7.4,2X,'DELTA=',F7.4)      
1000	CONTINUE
	RETURN
      END
