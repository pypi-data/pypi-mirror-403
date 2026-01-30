clear

t = 1; % hopping amplitude
N = 30; % chain length

% number of kept multiplets
Nkeep = (2.^(0:9)).'*10;

% ground-state enegy from iterative diagonalization
EG_iter = zeros(numel(Nkeep),2);

for itS = (1:2) % different symmetries
    if itS == 1
        [F,Z,S,I] = getLocalSpace('FermionS','Acharge,Aspin','NC',1);
    else
        [F,Z,S,I] = getLocalSpace('FermionS','Acharge,SU2spin','NC',1);
    end
    
    H0 = I.E*1e-30;
    H0.info.itags = {'s00','s00*'};
    A0 = getIdentity(getvac(H0),2,H0,2,[1 3 2]);
    A0.info.itags = {'L00','R00*','s00'};
    
    for itK = (1:numel(Nkeep))
        tobj = tic2;
        
        for itN = (1:N)
            % particle operator at the new site
            Fnow = F;
            for ito = (1:numel(Fnow))
                Fnow(ito).info.itags = {['s',sprintf('%02i',itN-1)], ...
                    ['s',sprintf('%02i',itN-1),'*'],'op*'};
            end
            
            if itN == 1
                % isometry for the current iteration
                Anow = A0;
                % Hamiltonian for the current iteration
                Hnow = contract(A0,'!2*',{H0,'!1',A0});
            else
                % add new site
                Anow = getIdentity(Aprev,2,I.E,2,[1 3 2]);
                Anow.info.itags(2:3) = ...
                    {['R',sprintf('%02i',itN-1),'*'], ...
                    ['s',sprintf('%02i',itN-1)]};

                % update the Hamiltonian up to the last sites
                % to the enlarged Hilbert space
                Hnow = contract(Anow,'!2*',{Hprev,'!1',Anow});

                % fermionic sign operator at the new site
                Znow = Z;
                Znow.info.itags = {['s',sprintf('%02i',itN-1)], ...
                    ['s',sprintf('%02i',itN-1),'*']};
                
                Hhop = QSpace;
                for ito = (1:numel(Fnow))
                    % hopping term from the last site to the new site
                    Hhop = Hhop + ...
                        contract(Anow,'!2*',{Fprev(ito),'!1', ...
                        {{Fnow(ito),'!2*',Znow},'!1',Anow}});
                end
                Hhop = (-t)*Hhop; % multiply hopping amplitude
                % add the hopping term from the new site
                % to the last site
                Hhop = Hhop+Hhop';

                Hnow = Hnow+Hhop;
            end
            
            % diagonalize Hamiltonian; Hermitianization is done within eigQS
            [Eeig,Ieig] = eigQS(Hnow,'Nkeep',Nkeep(itK),'deps',1e-10);
            Ieig.EK = QSpace(Ieig.EK); % convert struct -> QSpace object
            Ieig.AK = QSpace(Ieig.AK);
            
            Ieig.EK.info.itags = {['R',sprintf('%02i',itN-1)], ...
                ['R',sprintf('%02i',itN-1),'*']};
            Ieig.AK.info.itags = Ieig.EK.info.itags;
            
            if itN == N
                % lowest energy
                EG_iter(itK,itS) = Eeig(1,1);
            else
                % % to be used for the next iteration
                Hprev = diag(Ieig.EK); % Hamiltonian
                Aprev = contract(Anow,'!1',Ieig.AK,[1 3 2]); % isometry
                % particle operator
                Fprev = QSpace(numel(Fnow),1);
                for ito = (1:numel(Fnow))
                    Fprev(ito) = contract(Aprev,'!2*', ...
                        {Fnow(ito),'!1',Aprev},[1 3 2]);
                end
            end
        end
        
        if itS == 1
            disp(['Acharge,Aspin | Nkeep = ',sprintf('%i',Nkeep(itK))]);
        else
            disp(['Acharge,SU2spin | Nkeep = ',sprintf('%i',Nkeep(itK))]);
        end
        toc2(tobj,'-v');
    end
end

% semi-analytic result
Hsp = diag(-t+zeros(N-1,1),1);
Hsp = Hsp+Hsp';
D = eig((Hsp+Hsp')/2);
EG_single = sum(D(D<0))*2; % *2 due to two spins
