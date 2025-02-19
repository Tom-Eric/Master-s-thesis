# coding:utf-8 
from odbAccess import openOdb
import xlrd
import os
import xlwt
import step
from abaqus import *
from abaqusConstants import *
import regionToolset
from caeModules import *

fPath = os.getcwd() + r'\modelData.txt'
with open(fPath, 'r') as Mas:
    data = Mas.readlines()
path, caeName, modelName = data[0].strip('\n').replace(' ', ''), data[1].strip('\n').replace(' ', ''), data[2].strip('\n').replace(' ', '')
with open(path + '\loop.txt', 'r') as f:
    data = f.readlines()
loop = int(data[0]) - 1

######## Gets the design variable 设计变量获取子函数 #########
def get_data(dirCase, sheetNum):
    data = xlrd.open_workbook(dirCase)
    table = data.sheets()[sheetNum]
    nor = table.nrows
    nol = table.ncols
    dictO = {}
    for i in range(0, nor):
        eNum = table.cell_value(i, 0)
        xDen = table.cell_value(i, 1)
        dictO[eNum] = xDen
        yield dictO

######## main function 主函数 #########
if __name__ == '__main__':
    myMdb = openMdb(pathName=caeName + '.cae')
    mdl = myMdb.models[modelName]
    part = mdl.parts['Part-1']
    ems, nds = part.elements, part.nodes
    dict1 = {}
    dict2 = {}

    # 获取设计变量数据
    for i in get_data(path + '\ExM_Evo' + str(ems[-1].label) + '.xls', loop):
        dict1.update(i)
    for key,value in dict1.items():
        if dict2.__contains__(value):
            dict2[value].append(key)
        else:
            dict2[value]=[key]

    # 根据设计变量数据设置材料和截面
    penal = 3
    youngOld = 2.0e5
    indexMaterial = 0
    listDx = list(dict1.values())

    for j in listDx:
        young = j ** penal * youngOld
        indexMaterial += 1
        l = str(indexMaterial)
        ut=list(map(int,dict2[j]))
        mdl.Material('Material' + l).Elastic(((young, 0.3),))
        mdl.HomogeneousSolidSection('Sec' + l, 'Material' + l)
        part.SectionAssignment(part.SetFromElementLabels(name='Eset-' + modelName + l, elementLabels=ut, unsorted=True),
                               sectionName='Sec' + l)

    # 创建步骤 Step-1 并定义载荷
    mdl.StaticStep(name='Step-1', previous='Initial', nlgeom=ON)
    mdl.FieldOutputRequest('SEDensity', 'Step-1', variables=('ELSE',))
    mdl.HistoryOutputRequest('ExtWork', 'Step-1', variables=('ALLWK',))
    
    a = mdl.rootAssembly
    region = a.instances['Part-1-2'].sets['Set-fix']
    mdl.DisplacementBC(name='BC-1', createStepName='Step-1', 
    region=region, u1=0.0, u2=0.0, ur3=0.0, amplitude=UNSET, fixed=OFF, 
    distributionType=UNIFORM, fieldName='', localCsys=None)
    
    a = mdl.rootAssembly
    region = a.instances['Part-1-2'].sets['Set-load'] 
    mdl.ConcentratedForce(name='Load-1', createStepName='Step-1', region=region, cf2=-1000.0, distributionType=UNIFORM, field='', localCsys=None)

    # 提交作业并等待完成
    myJob = myMdb.Job('Design' + modelName + '_job' + str(loop), modelName)
    myJob.submit()
    myJob.waitForCompletion()

    # 打开 ODB 文件并获取结果
    odb = openOdb('Design' + modelName + '_job' + str(loop) + '.odb')
    

    elseV = odb.steps['Step-1'].frames[-1].fieldOutputs['ELSE'].values
    obj = odb.steps['Step-1'].historyRegions['Assembly ASSEMBLY'].historyOutputs['ALLWK'].data[-1][1]

    # 将结果写入 Excel 文件
    wb = xlwt.Workbook(encoding='utf-8')
    rSheet = wb.add_sheet('Sheet1')
    rawDc = {}    
    for en in elseV:
        rawDc[en.elementLabel] = en.data    
    num = list(rawDc.keys())
    val = list(rawDc.values())    
    for indexy in ems:
        indexny = indexy.label - 1
        rSheet.write(indexny, 0, num[indexny])
        rSheet.write(indexny, 1, val[indexny])    
    rSheet.write(0, 2, obj)
    wb.save('ELSEandALLWK.xls')
    
    odb.close()

    # 输出单元中心坐标
    if loop == 0:
        workbook = xlwt.Workbook(encoding='utf-8')
        sheet = workbook.add_sheet('EM_coordinates')
        c0 = {}

        for el in ems:
            ndc = el.connectivity
            c0[el.label] = [sum([nds[nd].coordinates[i] / len(ndc) for nd in ndc]) for i in range(3)]
            eu = int(el.label) - 1
            sheet.write(eu, 0, el.label)
            sheet.write(eu, 1, c0[el.label][0])
            sheet.write(eu, 2, c0[el.label][1])
            sheet.write(eu, 3, c0[el.label][2])

        workbook.save('EL_coordinateS.xls')

    # 添加载荷 Load-2 到 Step-1
    del mdl.loads['Load-1']
    mdl.ConcentratedForce(name='Load-2', createStepName='Step-1', region=region, cf2=-(1.01*1000.0), distributionType=UNIFORM, field='', localCsys=None)

    # 提交作业 2 并等待完成
    myJob2 = myMdb.Job('D' + modelName + '_job_case2_' + str(loop), modelName)
    myJob2.submit()
    myJob2.waitForCompletion()

    # 打开第二个 ODB 文件并获取结果
    odb2 = openOdb('D' + modelName + '_job_case2_' + str(loop) + '.odb')
    elseV2 = odb2.steps['Step-1'].frames[-1].fieldOutputs['ELSE'].values
    obj2 = odb2.steps['Step-1'].historyRegions['Assembly ASSEMBLY'].historyOutputs['ALLWK'].data[-1][1]

    # 将第二个结果写入第二个 Excel 文件
    wb2 = xlwt.Workbook(encoding='utf-8')
    rSheet2 = wb2.add_sheet('Sheet1')
    rawDc2 = {}

    for en in elseV2:
        rawDc2[en.elementLabel] = en.data

    num2 = list(rawDc2.keys())
    val2 = list(rawDc2.values())

    for indexy in ems:
        indexny = indexy.label - 1
        rSheet2.write(indexny, 0, num2[indexny])
        rSheet2.write(indexny, 1, val2[indexny])

    rSheet2.write(0, 2, obj2)
    wb2.save('ELSEandALLWK2.xls')
    odb2.close()
