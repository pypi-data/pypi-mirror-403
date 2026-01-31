!    -*- f90 -*-
! -*- coding: utf-8 -*-
! written by Ralf Biehl at the Forschungszentrum Juelich ,
! Juelich Center for Neutron Science 1 and Institute of Complex Systems 1
!    jscatter is a program to read, analyse and plot data
!    Copyright (C) 2020-2021  Ralf Biehl
!
!    This program is free software: you can redistribute it and/or modify
!    it under the terms of the GNU General Public License as published by
!    the Free Software Foundation, either version 3 of the License, or
!    (at your option) any later version.
!
!    This program is distributed in the hope that it will be useful,
!    but WITHOUT ANY WARRANTY; without even the implied warranty of
!    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
!    GNU General Public License for more details.
!
!    You should have received a copy of the GNU General Public License
!    along with this program.  If not, see <http://www.gnu.org/licenses/>.
!

module dynamic
    use typesandconstants
    use utils
    !$ use omp_lib
    implicit none

contains

    function bnmt(t, NN, l, mu, modeamplist, tp, fixedends)
        ! Rouse/Zimm mode summation in Bnm with [coherent.., incoherent.., modeamplitudes..]

        ! times, mu, modeamplitudes, relaxation times, bond length
        real(dp), intent(in) :: t(:), mu, modeamplist(:), tp(:), l
        ! number beads, fixedends of chain
        integer, intent(in)  :: NN, fixedends
        ! result (n*m,tcoh + tinc + 1 for t=inf +mode amplitudes)
        real(dp)             :: bnmt(NN*NN, 2*size(t) + 1 + size(modeamplist))
        ! internal stuff, mode numbers p, monomers n,m
        integer              :: p, n, m
        ! mode contributions
        real(dp)             :: pnm

        ! init
        bnmt = 0_dp

        !$omp parallel do
        do m = 1, NN
            do n = 1, NN
                do p = 1, size(modeamplist)
                    if (fixedends == 2) then
                        ! two fixed ends
                         pnm = modeamplist(p) * sin(pi_dp * p * n / NN) * sin(pi_dp * p * m / NN)
                    else if (fixedends == 1) then
                        ! one fixed end, one free
                         pnm = modeamplist(p) * sin(pi_dp * (p-0.5) * n / NN) * sin(pi_dp * (p-0.5) * m / NN)
                    else
                        ! two open ends as default , standeard Rouse/ZIMM
                        pnm = modeamplist(p) * cos(pi_dp * p * n / NN) * cos(pi_dp * p * m / NN)
                    end if

                    ! coherent part
                    bnmt((n-1)*NN+m, :size(t)) = bnmt((n-1)*NN+m, :size(t)) + pnm * (1 - exp(-t/tp(p)))

                    ! t =  infinity, exp decayed to zero
                    bnmt((n-1)*NN+m, 2*size(t)+1) = bnmt((n-1)*NN+m, 2*size(t)+1) + pnm

                    ! each p for mode amplitudes is sum_p( mode amplitudes)
                    bnmt((n-1)*NN+m, 2*size(t)+1+p) = bnmt((n-1)*NN+m, 2*size(t)+1+p) + pnm

                    if (n == m) then
                        ! incoherent part
                        bnmt((n-1)*NN+m,size(t):2*size(t)) = bnmt((n-1)*NN+m,size(t):2*size(t)) + pnm * (1-exp(-t/tp(p)))
                    end if
                end do
                bnmt((n-1)*NN+m,:) = bnmt((n-1)*NN+m,:) + (abs(n - m) ** (2 * mu) * l ** 2)
            end do
        end do
        !$omp end parallel do

    end function bnmt

    function fourierw2t(w, s, ds, t) result(fft)
        ! fourier transform freq domain data to time domain
        ! do explicit not FFT to allow non-equidistant data
        ! The instrument resolution works like a window function
        ! inspired by unift from Reiner Zorn

        ! w frequency 1/ns, measured S(w) , error of S(w)
        real(dp), intent(in) :: w(:), s(:), ds(:)
        ! times in ns
        real(dp), intent(in) :: t(:)
        ! result times x 5 = [times, S(t), error S(t), real S(t), imag S(t)]
        real(dp)             :: fft(size(t), 5)
        integer :: i

        !$omp parallel do
        DO i = 1, size(t)
            ! returns [times, S(t), error S(t), real S(t), imag S(t)]
            fft(i,:) = fourier(w, s, ds, t(i))
        END DO
        !$omp end parallel do

    end function fourierw2t

    function fourier(w, s, ds, t) result(fft)
        ! explicit fourier transform for one timepoint
        ! w frequency 1/ns, measured S(w) , error of S(w)
        ! inspired by unift from Reiner Zorn
        real(dp), intent(in) :: w(:), s(:), ds(:)
        ! time ns
        real(dp), intent(in) :: t
        ! size of w,s,ds
        integer :: n
        ! amplitudes internal
        real(dp) :: a1(size(w)), a2(size(w)), swt(size(w)), cwt(size(w)), dft2(size(w)), t2
        ! result [t, ft, dft, real ft, imag ft]
        real(dp)       :: fft(5), ft, dft, ft1, ft2

        n = size(w)
        if (t /= 0_dp) then
            swt = sin(w * t)
            cwt = cos(w * t)
            t2 = one_dp / (t*t)

            a1(1) = -swt(1)/t + (cwt(1)-cwt(2))/(w(2)-w(1)) * t2
            a2(1) =  cwt(1)/t + (swt(1)-swt(2))/(w(2)-w(1)) * t2
            ! do i=2,n-1
            !   a1(i)=((cwt(i)-cwt(i+1))/(w(i+1)-w(i)) + (cwt(i-1)-cwt(i))/(w(i-1)-w(i)))*t2
            a1(2:n-1) = ((cwt(2:n-1)-cwt(3:n))/(w(3:n)-w(2:n-1)) + (cwt(1:n-2)-cwt(2:n-1))/(w(1:n-2)-w(2:n-1)))*t2
            !   a2(i)=((swt(i)-swt(i+1))/(w(i+1)-w(i)) + (swt(i-1)-swt(i))/(w(i-1)-w(i)))*t2
            a2(2:n-1) = ((swt(2:n-1)-swt(3:n))/(w(3:n)-w(2:n-1)) + (swt(3:n-2)-swt(2:n-1))/(w(3:n-2)-w(2:n-1)))*t2
            ! end do
            a1(n) = swt(n)/t+(cwt(n-1)-cwt(n))/(w(n-1)-w(n))*t2
            a2(n) = -cwt(n)/t+(swt(n-1)-swt(n))/(w(n-1)-w(n))*t2
        else
            a1(1) = (w(2)-w(1))*0.5
            a2(1) = 0_dp
            !do i=2,n-1
            !   a1(i) = (w(i+1)-w(i-1)) * 0.5
            a1(2:n) = (w(3:n)-w(1:n-1)) * 0.5
            a2 = 0_dp
            ! end do
            a1(n) = (w(n) - w(n-1)) * 0.5
            a2(n) = 0_dp
        end if

        ft1 = sum(a1 * s)  ! real part
        ft2 = sum(a2 * s)  ! imag part
        ft = sqrt(ft1 * ft1 + ft2 * ft2)  ! absolute

        ! error propagation
        dft = sqrt(sum(((a1 * ft1 + a2 * ft2) / ft * ds)**2))

        fft(1) = t
        fft(2) = ft
        fft(3) = dft
        fft(4) = ft1
        fft(5) = ft2

    end function fourier

    function sqtnonlinearpolymer(evec, evals, mu, b, q, t, l, brc, loverR, ti) result(sqt)
        ! S(q,t) form eigenvalues and eigenvectors of HA matrix
        ! sqt will be internal contributions WITHOUT diffusion
        ! M. Guenza, A. Perico Macromolecules 1993, 26, 4196-4202
        ! calcs the S_I(q,t) of equation 3 with eigenvalues and eigenvectors as input
        !
        ! this is for the general case including scattering length densities for matching
        ! We summ over all given evals and evec given to the function
        ! skip first and later eigenvalue and eigenvector if these should not be used

        ! times, scattering vectors, scattering length, segment_length**2, bond rate constant, loverR, tinternal
        real(dp), intent(in) :: t(:), q(:), b(:), l, brc, loverR(:,:), ti
        ! eigenvalues, eigenvectors, mu=diag(evec.T @ A @ evec)
        ! The column evect[:, k] is the normalized eigenvector corresponding to the eigenvalue eval[k].
        real(dp), intent(in) :: evals(:), evec(:,:), mu(:)
        ! number beads
        integer              :: N
        ! dynamic distance matrix
        real(dp)             :: dij(size(evec,1), size(evec,1), size(t)+1)
        ! result: lt for times; lt+1 is for lt=inf; lt+2 for cumulant
        real(dp)             :: sqt(size(q), size(t)+2)
        ! internal stuff: monomers i,j; mode numbers k, q , lt=size(t)
        integer              :: i, j, k, iq, lt
        ! temp variable
        real(dp)             :: q2l26, rates(size(evals)), ticorrection

        N = size(evec,1)
        lt = size(t)

        call setncpu(0)

        ! dij(t) dynamic square distance matrix  equ. 8
        ! skip first eigenvalue is COM diffusion (k=2,size(evals))
        ! here we summ over all evals from calling function
        ! this is the only time consuming part
        dij = 0_dp  ! init

        rates = brc * evals / (1_dp + brc * evals * ti)

        !$omp parallel do private(j, k)
        do i=1,N
            ! only upper part j>=i and i==j is zero for all times, lower part is not used below for sqt
            do j=i,N
                do k = 1, size(evals)
                    ! static part
                    dij(i,j,1:lt+1) = dij(i,j,1:lt+1) +  (evec(i,k)**2 + evec(j,k)**2 ) / mu(k)
                    ! time dependence; lt+1 will be for t=inf with exp(-inf)=0
                    dij(i,j,1:lt  ) = dij(i,j,1:lt) - 2 * evec(i,k)*evec(j,k) / mu(k) * exp(-rates(k) * t)
                enddo
            enddo
        enddo
        !$omp end parallel do

        ! calc sqt  for all Q from above
        ! lt+2 for sum in cumulant expression equ 13
        sqt = 0_dp  ! init
        ! ticorrection for cumulant if ti >0
        if (ti>0) then
            ticorrection = sum(1/ (1 + brc * evals * ti))
        else
            ticorrection = 1_dp
        end if
        !$omp parallel do private(q2l26, i, j)
        do iq= 1, size(q)
            q2l26 = q(iq) * q(iq) * l*l / 6_dp
            do i=1,N
                do j=i,N
                    if (i/=j) then
                        ! equ 3 to be general and not only stars; lt+1 is t=inf
                        ! use symmetry in i,j if i/=j -> factor 2
                        sqt(iq, 1:lt+1) = sqt(iq, 1:lt+1) + 2 * exp(- q2l26 * dij(i,j,:)) * b(i)*b(j)
                        ! for Dcm calc the sum_{ij} in equ 13
                        ! i/=j  is (1-delta_ij)
                        ! cumulant in lt+2: dij(i,j,1) is t=0 in equ 13
                        sqt(iq, lt+2) = sqt(iq, lt+2) + 2 * b(i)*b(j) * loverR(i,j) * ticorrection * exp(-q2l26 * dij(i,j,1))
                    else
                        ! add the i==j term only once
                        sqt(iq, 1:lt+1) = sqt(iq, 1:lt+1) + b(i)*b(j) * exp(- q2l26 * dij(i,j,:))
                    endif
                enddo
            enddo
        enddo
        !$omp end parallel do

    end function sqtnonlinearpolymer

    function eigvector2rij2(eval, evec) result(rij)
        ! A hierarchy of models for the dynamics of polymer chains in dilute solution
        ! Perico JChemPhys 87,3677 (1987)
        ! equation  3.1 upper static part
        ! first eigenvalue is ignored as it should be zero for center of mass diffusion
        ! assuming sorted eigenvalues

        ! eigenvalues , eigenvectors
        ! The column evect[:, i] is the normalized eigenvector corresponding to the eigenvalue eval[i].
        real(dp), intent(in) :: eval(:), evec(:,:)
        ! indices
        integer              :: i, j, k
        ! result
        real(dp)             :: rij(size(evec,1),size(evec,1))

        rij = 0.0_dp  ! init

        do i=1,size(rij,1)
            do j=1,size(rij,2)
                if (i/=j) then  ! just avoid adding zero
                    rij(i,j) = sum((evec(i,2:) - evec(j,2:))**2 / eval(2:))
                endif
            end do
        end do

    end function eigvector2rij2

    function cumcos(multi, i, j) result(prod)
        ! A cumulative product over values in cos from position i to pos j
        ! cos contains floats to  multiply and i,j contain indices zero based for start and end position in cos
        ! values smaller 0.001 set to zero

        real(dp), intent(in) :: multi(:)
        integer, intent(in) :: i(:,:), j(:,:)
        ! indices
        integer              :: m, n
        ! result
        real(dp)             :: prod(size(i,1),size(i,2)), p

        prod = 0.0_dp  ! init

        do m=1,size(i,1)
            do n=1,size(i,2)
                if (i(m,n) < j(m,n)) then
                    p = product(multi(i(m,n)+1:j(m,n)))
                elseif (i(m,n) > j(m,n)) then
                    p = product(multi(j(m,n)+1:i(m,n)))
                else
                    p=1  ! m==n
                end if
                if (p > 0.001_dp) then
                    prod(m,n) = p
                end if
            end do
        end do

    end function cumcos

end module dynamic