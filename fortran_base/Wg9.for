C=    FILE NAME MATH.FOR
C ############################################################
C 高斯消元子程序
C 与床的结构和几何尺寸无关!!!
C ############################################################
      SUBROUTINE GAUSLL(ND,NCOL,N,NS,A,NFEHL)
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      DIMENSION A(ND,NCOL)

      NFEHL=0
      N1=N+1
      NT=N+NS
      IF (N.EQ.1) GOTO 50
      DO 10 I=2,N
         IP=I-1
         I1=IP
         X=DABS(A(I1,I1))
         DO 11 J=I,N
         IF (DABS(A(J,I1)).LT.X) GOTO 11
         X=DABS(A(J,I1))
         IP=J
 11      CONTINUE
         
	   IF (IP.EQ.I1) GOTO 13
         DO 12 J=I1,NT
         X=A(I1,J)
         A(I1,J)=A(IP,J)
 12      A(IP,J)=X

 13      DO 10 J=I,N
         IF (DABS(A(J,I1)).GT.1.0D-20) THEN
            X=A(J,I1)/A(I1,I1)
            DO 15 K=I,NT
               IF (DABS(A(I1,K)).GT.1.0D-20) THEN
                  A(J,K)=A(J,K)-X*A(I1,K)
               ENDIF
 15         CONTINUE
         ENDIF
 10   CONTINUE

 50   DO 20 IP=1,N
         I=N1-IP
         IF (DABS(A(I,I)).LT.1.0D-20) A(I,I)=1.0D-20
         DO 20 K=N1,NT
            A(I,K)=A(I,K)/A(I,I)
            IF (I.EQ.1) GOTO 20
            I1=I-1
            IF (DABS(A(I,K)).GT.1.0D-20) THEN
               DO 25 J=1,I1
                  IF (DABS(A(J,I)).GT.1.0D-20) THEN
                     A(J,K)=A(J,K)-A(I,K)*A(J,I)      
                  ENDIF
 25            CONTINUE
            ENDIF
 20   CONTINUE

      RETURN
 100  NFEHL=1
      RETURN
      END


C ############################################################
C 矩阵相加子程序
C 与床的结构和几何尺寸无关!!!
C ############################################################
      FUNCTION MATADD(NF,NG,MATIN1,NAN1X,MATIN2,NAN2X,MATOUT,
     &             NDI1,NDI2)
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      DOUBLE PRECISION MATIN1(NF,NDI1),MATIN2(NF,NDI2),
     &                 MATOUT(NF,NDI1)
      DO 1 I=1,NAN1X
      DO 1 K=1,NG
         MATOUT(K,I)=MATIN1(K,I)+MATIN2(K,I)
    1 CONTINUE
      MATADD=0
      NYXU=NAN2X
      RETURN
      END


C ############################################################
C 矩阵相减子程序
C 与床的结构和几何尺寸无关!!!
C ############################################################
      FUNCTION MATSUB(NF,NG,MATIN1,NAN1X,MATIN2,NAN2X,MATOUT,
     &             NDI1,NDI2)
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      DOUBLE PRECISION MATIN1(NF,NDI1),MATIN2(NF,NDI2),
     &                 MATOUT(NF,NDI1)
      DO 2 I=1,NAN1X
      DO 2 K=1,NG
         MATOUT(K,I)=MATIN1(K,I)-MATIN2(K,I)
    2 CONTINUE
      MATSUB=0
      NMH=NAN2X
      RETURN
      END

C ############################################################
C 矩阵相乘子程序
C 与床的结构和几何尺寸无关!!!
C ############################################################
      FUNCTION MATMULT(NF,NG,MATIN1,NAN1X,MATIN2,NAN2X,MATOUT,
     &                 NDI1,NDI2)
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      DOUBLE PRECISION MATIN1(NF,NDI1),MATIN2(NF,NDI2),
     &                 MATOUT(NF,NDI1)
      DO 3333 I=1,NAN1X
      DO 3333 K=1,NG
         MATOUT(K,I)=0.0
 3333 CONTINUE    

      DO 1310 I=1,NAN1X
      DO 1310 L=1,NG
	   QEL=MATIN1(L,I)
	   IF (DABS(QEL).GT.1.0D-20) THEN
	      DO 1311 K=1,NG
 1311       MATOUT(K,I)=MATOUT(K,I)+QEL*MATIN2(K,L)
	   ENDIF
 1310 CONTINUE

      MATMULT=0
      NXX1=NAN2X
      RETURN
      END


C ############################################################
C 矩阵相除子程序
C 与床的结构和几何尺寸无关!!!
C ############################################################
      FUNCTION MATDIV(NF,NG,MATIN1,NAN1X,MATIN2,NAN2X,MATOUT,
     &                NDI1,NDI2)
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      DOUBLE PRECISION MATIN1(NF,NDI1),MATIN2(NF,NDI2),
     &                 MATOUT(NF,NDI1),ZMAT(NF,2*NF)
      INCLUDE 'COMMON.00'
C      DIMENSION ZMAT(9,18)
C      DIMENSION ZMAT(10,20)
C      DATA NRECH,NRECH2/10,20/
	NRECH=NF
	NRECH2=2*NF
      IF (NG.GE.2) GOTO 4
      MATOUT(1,1)=MATIN1(1,1)/MATIN2(1,1)
      MATDIV=0
      RETURN

 4    NNIN1=NAN1X
      NNIN2=NAN2X
      
	IF (NNIN1.LT.0) NNIN1=-NNIN1
      IF (NNIN2.LT.0) NNIN2=-NNIN2
      IF (NAN2X.LT.0) GOTO 6
      DO 5 I=1,NNIN2
	   DO 5 K=1,NG
	   ZMAT(I,K)=MATIN2(I,K)
 5    CONTINUE
      GOTO 8
 6    DO 7 I=1,NNIN2
	   DO 7 K=1,NG
	   ZMAT(I,K)=MATIN2(K,I)
 7    CONTINUE

 8    IF (NAN1X.LT.0) GOTO 10
      DO 9 I=1,NNIN1
	DO 9 K=1,NG
	   ZMAT(K,NNIN2+I)=MATIN1(K,I)
 9    CONTINUE
      GOTO 12
 
 10   DO 11 I=1,NNIN1
	DO 11 K=1,NG
	   ZMAT(K,NNIN2+I)=MATIN1(I,K)
 11   CONTINUE

 12   CALL GAUSLL(NRECH,NRECH2,NNIN2,NNIN1,ZMAT,NFEHL)
      MATDIV=NFEHL
      IF (MATDIV.NE.0) RETURN
      IF (NAN1X.LE.0) GOTO 15

      DO 14 I=1,NNIN1
	DO 14 K=1,NG
	   MATOUT(K,I)=ZMAT(K,NNIN2+I)
 14   CONTINUE
      RETURN

 15   DO 16 I=1,NNIN1
	DO 16 K=1,NG
	   MATOUT(I,K)=ZMAT(K,NNIN2+I)
 16   CONTINUE
      RETURN
      END


C ############################################################
C 矩阵截断子程序
C 与床的结构和几何尺寸无关!!!
C ############################################################
      FUNCTION MATUMS(NF,NMAT,MATIN1,NMAT1,NX1,MX1,MATOUT,
     &                NMAT2,NXU1)
	IMPLICIT DOUBLE PRECISION (A-H,O-Z)
	DOUBLE PRECISION MATIN1(NF,NMAT),MATOUT(NF,NMAT)

	NXX=NX1
	NXX=MX1
	NXX=NXU1

      DO 13 I=1,NMAT
	DO 13 K=1,NMAT
	   MATOUT(K,I)=MATIN1(K,I)
   13 CONTINUE
      
	MATUMS=0
      RETURN
      END
C ############################################################
C 子程序与床的结构和几何尺寸无关!!!
C ############################################################
      SUBROUTINE KOLON1
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      INCLUDE 'COMMON.00'
      INCLUDE 'COMMON.01'
      INCLUDE 'COMMON.02'
      INCLUDE 'COMMON.03'
      
       DTMAX=100.5
       DGMAX1=0.051
       DGMAX2=0.001
       DGMAX3=0.02
       DGMAX4=0.052
       DGMAX5=0.008
       DGMAX6=0.01
       DGMAX7=0.1
       DGMAX8=0.1
       DXMAX=0.051
       DWMAX=0.2
      
	SUMFE=0.
      DO 10 I=NZEL1,NZEL2
      DO 11 J=1,NVE
 11   SUMFE=SUMFE+DABS(DMAT(J,I))
 10   CONTINUE
      IF(SUMFE.GT.SKONFE) KONVER=1
      DO 13 I=NZEL1,NZEL2
      IF(DABS(DMAT(1,I)).GT.DGMAX1) FEMF(1,I)=FEMF(1,I)+
     &   DMAT(1,I)*DGMAX1/DABS(DMAT(1,I))
      IF(DABS(DMAT(1,I)).LT.DGMAX1) FEMF(1,I)=FEMF(1,I)+DMAT(1,I)
      IF(DABS(DMAT(2,I)).GT.DGMAX2) FEMF(2,I)=FEMF(2,I)+
     &   DMAT(2,I)*DGMAX2/DABS(DMAT(2,I))
      IF(DABS(DMAT(2,I)).LT.DGMAX2) FEMF(2,I)=FEMF(2,I)+DMAT(2,I)
      IF(DABS(DMAT(3,I)).GT.DGMAX3) FEMF(3,I)=FEMF(3,I)+
     &   DMAT(3,I)*DGMAX3/DABS(DMAT(3,I))
      IF(DABS(DMAT(3,I)).LT.DGMAX3) FEMF(3,I)=FEMF(3,I)+DMAT(3,I)
      IF(DABS(DMAT(4,I)).GT.DGMAX4) FEMF(4,I)=FEMF(4,I)+
     &   DMAT(4,I)*DGMAX4/DABS(DMAT(4,I))
      IF(DABS(DMAT(4,I)).LT.DGMAX4) FEMF(4,I)=FEMF(4,I)+DMAT(4,I)
      IF(DABS(DMAT(5,I)).GT.DGMAX5) FEMF(5,I)=FEMF(5,I)+
     &   DMAT(5,I)*DGMAX5/DABS(DMAT(5,I))
      IF(DABS(DMAT(5,I)).LT.DGMAX5) FEMF(5,I)=FEMF(5,I)+DMAT(5,I)
      IF(DABS(DMAT(6,I)).GT.DGMAX6) FEMF(6,I)=FEMF(6,I)+
     &   DMAT(6,I)*DGMAX6/DABS(DMAT(6,I))
      IF(DABS(DMAT(6,I)).LT.DGMAX6) FEMF(6,I)=FEMF(6,I)+DMAT(6,I)
      IF(DABS(DMAT(7,I)).GT.DGMAX7) FEMF(7,I)=FEMF(7,I)+
     &   DMAT(7,I)*DGMAX7/DABS(DMAT(7,I))
      IF(DABS(DMAT(7,I)).LT.DGMAX7) FEMF(7,I)=FEMF(7,I)+DMAT(7,I)
      IF(DABS(DMAT(8,I)).GT.DGMAX8) FEMF(8,I)=FEMF(8,I)+
     &   DMAT(8,I)*DGMAX8/DABS(DMAT(8,I))
      IF(DABS(DMAT(8,I)).LT.DGMAX8) FEMF(8,I)=FEMF(8,I)+DMAT(8,I)
      DO 13 J=1,8
      IF(FEMF(J,I).LT.0.0) FEMF(J,I)=0.0
  13  CONTINUE
      
	SUMWE=0.
      NG1=NVE+1
      DO 60 I=NZEL1,NZEL2
  60  SUMWE=SUMWE+DABS(DMAT(NSGP,I))
      IF(SUMWE.GT.SKONWE) KONVER=1
      
	DO 63 I=NZEL1,NZEL2
      IF(DABS(DMAT(NSGP,I)).GT.DWMAX) WE(I)=WE(I)
     &    +DMAT(NSGP,I)*DWMAX/DABS(DMAT(NSGP,I))
      IF(DABS(DMAT(NSGP,I)).LT.DWMAX) WE(I)=WE(I)
     &    +DMAT(NSGP,I)
      IF(WE(I).LE.0.D00) WE(I)=1.0D-20
 63   CONTINUE

	SUMX=0.
      NG1=NSGP+1
      DO 40 I=NZEL1,NZEL2
  40  SUMX=SUMX+DABS(DMAT(NSGP1,I))
      IF(SUMX.GT.SKONX) KONVER=1
      
	DO 43 I=NZEL1,NZEL2
      IF(DABS(DMAT(NSGP1,I)).GT.DXMAX) X(I)=X(I)
     &    +DMAT(NSGP1,I)*DXMAX/DABS(DMAT(NSGP1,I))
      IF(DABS(DMAT(NSGP1,I)).LT.DXMAX) X(I)=X(I)
     &    +DMAT(NSGP1,I)
      IF(X(I).LE.0.D00) X(I)=1.0D-20
      IF(X(I).GT.1.0)   X(I)=1.0
 43   CONTINUE
      
	SUMT=0.
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
	IF(KTRLT.NE.1) GOTO 54
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
      NG2=NG1+1
      DO 50 I=NZEL1,NZEL2
 50   SUMT=SUMT+DABS(DMAT(NG2,I))
      IF(SUMT.GT.SKONT) KONVER=1
      DO 53 I=NZEL1,NZEL2
      IF(DABS(DMAT(NG2,I)).GT.DTMAX) T(I)=T(I)+
     &    DMAT(NG2,I)*DTMAX/DABS(DMAT(NG2,I))
      IF(DABS(DMAT(NG2,I)).LT.DTMAX)T(I)=T(I)+DMAT(NG2,I)
C      IF(T(I).LE.298.) T(I)=298.
      IF(T(I).GT.3000.0) T(I)=3000.0
 53   CONTINUE
54	CONTINUE
C      IF(ITERAT.EQ.1) WRITE(1,49)
      IF(ITERAT.EQ.1) WRITE(*,49)
 49    FORMAT(1X,//2X,'KONVER',8X,'SUMFE',10X,'SUMWE',8X,'SUMX',8X,
     &   'SUMT',8X,'ITERAT',/)
      Y02=FEMF(1,1)/FEM(1)
C      WRITE(1,51) KONVER,SUMX,SUMFE,SUMT,ITERAT
      WRITE(*,51) KONVER,SUMFE,SUMWE,SUMX,SUMT,ITERAT
 51    FORMAT(2X,'KONVER=',I3,4E13.4,4X,I3)
 44   CONTINUE
      RETURN
      END

C ############################################################
C 牛顿-拉姆森求解子程序
C 与床的结构和几何尺寸无关!!!
C ############################################################
      SUBROUTINE NEWTRA
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      INCLUDE 'COMMON.00'
      INCLUDE 'COMMON.03'

	IF(KTRLT.EQ.1) THEN
	NEQN=NVWS
	ELSE
	NEQN=NVWS-1
	ENDIF
      CALL BLKTRD(NEQN,NZEL2)      
      CALL KOLON1
      RETURN
      END

      SUBROUTINE BLKTRD(NMAT,NST)
      IMPLICIT DOUBLE PRECISION (A-H,O-Z)
      INCLUDE 'COMMON.00'
      INCLUDE 'COMMON.03'
C      COMMON /MATRX4/  ZWMAT(10,10),ZWVEK(10),
      DIMENSION  ZWMAT(NMAT,NMAT),ZWVEK(NMAT)
      NF=NMAT
      IS=0
      DO 1 I=2,NST
      IS=IS+MATDIV(NF,NMAT,AMAT(1,1,I-1),-NMAT,BMAT(1,1,I-1),-NMAT,
     &             AMAT(1,1,I-1),NMAT,NMAT)
      IS=IS+MATMULT(NF,NMAT,CMAT(1,1,I-1),NMAT,AMAT(1,1,I-1),
     &             NMAT,ZWMAT,NMAT,NMAT)


      IS=IS+MATSUB(NF,NMAT,BMAT(1,1,I),NMAT,ZWMAT,NMAT,BMAT(1,1,I),
     &             NMAT,NMAT)
      IS=IS+MATMULT(NF,NMAT,DMAT(1,I-1),1,AMAT(1,1,I-1),NMAT,ZWVEK,
     &              1,NMAT)
      IS=IS+MATSUB(NF,NMAT,DMAT(1,I),1,ZWVEK,1,DMAT(1,I),1,1)
    1 CONTINUE

      DO 2 K=1,NST
      I=NST+1-K
      IF (I.EQ.NST) GOTO 3
      IS=IS+MATMULT(NF,NMAT,DMAT(1,I+1),1,CMAT(1,1,I),NMAT,ZWVEK,
     &             1,NMAT)
      IS=IS+MATSUB(NF,NMAT,DMAT(1,I),1,ZWVEK,1,DMAT(1,I),1,1)
    3 IS=IS+MATDIV(NF,NMAT,DMAT(1,I),1,BMAT(1,1,I),NMAT,DMAT(1,I),
     &             1,NMAT)
    2 CONTINUE
	IF (IS.NE.0) STOP' BLKTRD'
      RETURN
      END
