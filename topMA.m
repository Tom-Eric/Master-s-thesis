 %%%%%%%Calling ABAQUS for FEA topology optimization code based on SIMP method 基于 SIMP 法通% % 过调用 ABAQUS 进行有限元分析的 MATLAB 基础程序%%%%%%%
% function topMA(maxElNum,volfrac,penal,rmin) 
maxElNum=6400;volfrac=0.4;penal=3;rmin=30;
path = 'E:\Lbrack';
caeName = 'LBeam';
modelName = 'L-bracket';
rfid = fopen([path,'\result_elenum',num2str(maxElNum),'.txt'],'w');
data = strvcat(path,caeName,modelName);
dfid = fopen([path,'\modelData.txt'],'w');
[m,~] = size(data);
for k = 1:m
    fprintf(dfid,'%s\n%s\n%s\n%s\n',data(k,:));
end
fclose(dfid);
parent_dir_name ='GNTO results';
if  exist(parent_dir_name,"dir") 
rmdir(parent_dir_name, 's') % Delete the existed file
end
mkdir(parent_dir_name);
x = ones(maxElNum,1)*volfrac;
EmlN = [1:1:maxElNum]';
loop = 0; 
change = 1.;
%%%%% Start of cycle 进入循环%%%%%%%
while change > 0.01 
 loop = loop + 1;
 lfid = fopen([path,'\loop.txt'],'w+');
 fprintf(lfid,'%d',loop);
 fclose(lfid);
 xold = x;
 cd(path);
%  showDensity(100,40,x); 
%  FileName=[parent_dir_name,'\Fig_',int2str(loop), '.png'];     saveas(gcf,FileName);
 xlswrite(['ExM_Evo',num2str(maxElNum),'.xls'],EmlN,loop,'A1');
 xlswrite(['ExM_Evo',num2str(maxElNum),'.xls'],x,loop,'B1');
 warning off MATLAB:xlswrite:AddSheet;
 system('abaqus cae noGUI=abaOutputv3.py');
 c = 0.;
 dc = zeros(maxElNum,1);
 ELSE = readmatrix('ELSEandALLWK.xls');
 ELSE2 = readmatrix('ELSEandALLWK2.xls');
dstrain_energy=ELSE2(:,2)-ELSE(:,2);
for i=1:maxElNum
    dc(i)=-100*dstrain_energy(i,1)*penal/x(i);
end
 c = c+ELSE(1,3)*2;
 dc=min(dc,0);
 [dc] = check(maxElNum,rmin,x,dc);
 [x] = OC(maxElNum,x,volfrac,dc);
 change = max(max(abs(x-xold)));
 disp([' It.: ' sprintf('%4i',loop) ' Obj.: ' sprintf('%10.4f',c) ...
 ' Vol.: ' sprintf('%6.3f',sum(sum(x))/(maxElNum)) ...
 ' ch.: ' sprintf('%6.3f',change )])
 fprintf(rfid,[' \n It.: ' sprintf('%4i',loop) '   Obj.: ' sprintf('%10.4f',c) ...
 '   Vol.: ' sprintf('%6.3f',sum(sum(x))/(maxElNum)) ...
 '   ch.: ' sprintf('%6.3f',change )]);
 
end 
fclose(rfid);
 %%%%%%% OPTIMALITY CRITERIA UPDATE 设计变量更新子程序%%%%%%%%%%%
function [xnew] = OC(maxElNum,x,volfrac,dc) 
l1 = 0; l2 = 100000; move = 0.2;
while (l2-l1 > 2e-2)
 lmid = 0.5*(l2+l1);
 xnew = max(0.001,max(x-move,min(1.,min(x+move,x.*sqrt(-dc./lmid)))));
 if sum(sum(xnew)) - volfrac*maxElNum > 0 
 l1 = lmid;
 else
 l2 = lmid;
 end
end
end
%%%%%%%%%% MESH-INDEPENDENCY FILTER 网格过滤子程序%%%%%%%%%%%%%%%
function[dcn] = check(maxElNum,rmin,x,dc) 
oData = xlsread('EL_coordinateS.xls');
vMax = max(oData);
vMin = min(oData);
if vMax(4) == vMin(4)
 p = 3;
else
 p = 4;
end
numArrays = p-1;
S = cell(numArrays,1);
dcn = zeros(maxElNum,1);
for i = 1:maxElNum
suma = 0;
 major = oData(i,:);
     for k =2:p
     [rowa,~] = find(oData(:,k)>oData(i,k)-(rmin+1) & oData(:,k)<oData(i,k)+(rmin+1));
     S{k-1} = [rowa];
     end
 if p == 3
 eleO = intersect(S{1},S{2});
 else
 eleO = intersect(intersect(S{1},S{2}),S{3});
 end
 for j = 1:length(eleO)
 minor = oData(eleO(j),:);
     dis = sqrt((major(2)-minor(2))^2+(major(3)-minor(3))^2+(major(4)-minor(4))^2);
     if rmin-dis>0
     fac = rmin-dis;
     suma = suma+max(0,fac);
     dcn(i,1) = dcn(i,1)+max(0,fac)*x(eleO(j),1)*dc(eleO(j),1);
     end
 end
 dcn(i,1) = dcn(i,1)/(x(i,1)*suma);
end
end
% end