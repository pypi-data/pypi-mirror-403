N = 50; % maximum chain length
Nkeep = 300; % maximal number of states to keep
tol = Nkeep*100*eps; % numerical tolerance for degeneracy

[S,I] = getLocalSpace('Spin',1/2);

H0 = I*0; % Hamiltonian for only the 1st site
A0 = getIdentity(1,2,I,2); % 1st leg is dummy leg (vacuum)

% lowest energies at each iteration
E0 = zeros(1,N);

for itN = (1:N)
    if itN == 1
        Hnow = H0;
        [V,D] = eig((Hnow+Hnow')/2);
        AK = contract(A0,3,3,V,2,1);
        E0(itN) = min(diag(D));
        Hprev = D;
    else
        % % add new site
        Anow = getIdentity(Hprev,2,I,2);
        Hnow = updateLeft(Hprev,2,Anow,[],[],Anow);
        % update the Hamiltonian up to the last sites
        % to the enlarged Hilbert space
        
        % % spin-spin interaction
        % Hermitian conjugate of the spin operator at
        % the current site
        Sn = permute(conj(S),[3 2 1]);
        HSS = updateLeft(Sprev,3,Anow,Sn,3,Anow);
        HSS = J*HSS;
        
        Hnow = Hnow+HSS;
        
        [V,D] = eig((Hnow+Hnow')/2);
        % sort eigenvalues and eigenvectors in the order of increasing
        % eigenvalues
        [D,ids] = sort(diag(D),'ascend');
        V = V(:,ids);
        
        E0(itN) = min(D);
        
        % truncation threshold for energy
        Etr = D(min([numel(D);Nkeep]));
        oks = (D < (Etr + tol));
        % true: to keep, false: not to keep
        % keep all degenerate states up to tolerance
        
        AK = contract(Anow,3,3,V(:,oks),2,1);
        Hprev = diag(D(oks));
    end
    
    % spin operator at the current site; to be used for 
    % generating the coupling term at the next iteration
    Sprev = updateLeft([],[],AK,S,3,AK);
    
    disptime(['#',sprintf('%02i/%02i',[itN,N]),' : ', ...
        'NK=',sprintf('%i/%i',[size(AK,3),size(Hnow,2)])]);
end

EG_iter = E0./(1:N);
Eexact = (1/4)-log(2); % exact GS energy, for infinite N
