import pandas as pd
import datetime


def check_mo(doct_ID, location, filial, df_dir_main_doct, pilot):
    if (location != df_dir_main_doct['Основное/ДОП место работы (название по выгрузке)'][doct_ID]
        and location != df_dir_main_doct['Основное/ДОП место работы (название по выгрузке).1'][doct_ID]
        and location != df_dir_main_doct['Основное/ДОП место работы (название по выгрузке).2'][doct_ID]
        and location != df_dir_main_doct['Основное/ДОП место работы (название по выгрузке).3'][doct_ID]
        or (doct_ID == 'Юрченко Евгений Гаврилович' and str(filial) != 'nan')):
        return True
    if (pilot[0] != 'Внепилот'):
        return True
    return False


def check_pilot(df_dir_MO, MO, pilot):
    if (not df_dir_MO.loc[lambda x: x['Наименование МО'] == MO].loc[lambda x: x['Пилот'] == 'в пилоте'].empty):
        pilot[0] = 'Пилот'
    elif (not df_dir_MO.loc[lambda x: x['Наименование МО'] == MO].loc[lambda x: x['Пилот'] == 'ДОП МО'].empty):
        pilot[0] = 'ДОП МО'
    return


def check_aktc(df_dir_MO, MO, pilot, filial):
    if (not df_dir_MO.loc[lambda x: x['МО'] == MO].loc[lambda x: x['Филиал'] == filial].empty):
        pilot[0] = 'АКТЦп'
    return



def check(data, doct_ID, location, df_date, df_dir_main_doct, filial, reason, pilot):

    i = 0
    if (df_dir_main_doct['Дата начала работы'][doct_ID] <= data):

        if ((not df_date.loc[lambda x: x['ФИО'] == doct_ID].loc[lambda x: x['Дата'] == data].empty) 
            or (not df_date.loc[lambda x: x['ФИО'] == doct_ID].loc[lambda x: x['Смена'] == 'Ночь'].loc[lambda x: x['Дата'] 
            + datetime.timedelta(days=1) == data].empty)):
            if (check_mo(doct_ID, location, filial, df_dir_main_doct, pilot) is True):
                reason[0] = 1
                return True
            else:
                reason[0] = 'МО'

        else:
            reason[0] = 'Табель'
        
    else:
        reason[0] = 'Не работал'

    return False


def count(df_test,  df_dir_MO, df_dir_main_doct, df_dir_an_spheres, df, do_pmu_contract, 
        do_pmu_no_contract, do_oms, df_date, df_oms, df_pmu, df_dir_pmu_contracts, df_dir_aktc):
    
    #print(df_test['Наименование услуги'])
    if (df_test['Дата визирования'] < df_test['Дата создания заключения']):
        df_test['Дата визирования'], df_test['Дата создания заключения'] = df_test['Дата создания заключения'], df_test['Дата визирования']

    pay = df_test['Тип оплаты окончательный']

    if (df_test['Модальность'] == 'КТ' or df_test['Модальность'] == "МРТ"):
        try:
            sphere = df_dir_an_spheres['Тип услуги'][df_test['Наименование услуги']]
            sphere_s = df_test['Модальность']
        except:
            print(df_test['Модальность'], "\"" + df_test['Наименование услуги'] + "\"")
            if (df_test['Модальность'].find('КТ') != -1):
                sphere = "КТ с КУ 1 зона"
            else:
                sphere = "МРТ 1 зона"
            sphere_s = df_test['Модальность']


    elif(df_test['Модальность'] == 'ММГ' and df_test['Наименование услуги'] == 'Скрининг рака молочной железы с помощью маммографии'):
        sphere = 'СРМЖ'
        sphere_s = 'СРМЖ'

    else:
        if (df_test['Наименование услуги'].lower().find("денситометрия") != -1):
            sphere = "Денс"
            sphere_s = "Денс"

        elif(df_test['Наименование услуги'].lower().find('флюорография') != -1):
            sphere = 'ФЛГ'
            sphere_s = "ФЛГ"

        else:
            sphere = df_test['Модальность']
            sphere_s = df_test['Модальность']

    if (str(sphere) == "МРТ 1 зона" or str(sphere) == "МРТ 2 и более зон" or str(sphere) == "МРТ 2 зоны"):
        sphere = "МРТ"

    data = df_test['Дата визирования']
    location = df_test['МО']
    filial = df_test['Филиал']
    pilot = ['Внепилот']
    aktc = ['Не АКТЦ']
    check_pilot(df_dir_MO, location, pilot)
    check_aktc(df_dir_aktc, location, aktc, filial)
    df_test['Пилот'] = pilot[0]
    df_test['АКТЦ'] = aktc[0]
    df_test['Тип услуги'] = sphere_s

    if (str(df_test['Врач-эксперт']) != "nan" and str(df_dir_main_doct['Место локации'][df_test['Врач-эксперт']]) != 'nan'):
        data = df_test['Дата создания заключения']
        data_exp = df_test['Дата визирования']
        i = df_pmu.loc[lambda x: x['Дата начала периода'] <= data_exp].loc[lambda x: x['Дата окончания периода'] >= data_exp].index
        start = str(df_oms['Дата начала периода'][i])[4:14]
        end = str(df_oms['Дата окончания периода'][i])[4:14]
        df_test['Неделя эксперты'] = start[8:10] + '.' + start[5:7] + '.' + start[0:4] + '-' +(
                                    end[8:10] + '.' + end[5:7] + '.' + end[0:4])
        sphere_exp = sphere + ".эксперты"
        
        doct_ID = df_test['Врач-эксперт']

        if (str(df_dir_main_doct['Место локации'][doct_ID]) == 'МРЦ'):
            reason = ['']
            if (check(data_exp, doct_ID, location, df_date, df_dir_main_doct, filial, reason, pilot) is True):
                if(sphere == 'ФЛГ'):
                    df[sphere_exp][df_test['Врач-эксперт']] += 1
                    if (pay != 'ОМС'):
                        if (not df_dir_pmu_contracts.loc[lambda x: x['МО'] == location].empty):
                            do_pmu_contract[sphere_exp][df_test['Врач-эксперт']] += 1
                        else:
                            do_pmu_no_contract[sphere_exp][df_test['Врач-эксперт']] += 1
                    else:
                        do_oms[sphere_exp][df_test['Врач-эксперт']] += 1
                df_test['Эксперт берем'] = 1

                

            else:
                df_test['Эксперт берем'] = reason[0]

            """elif (df_dir_main_doct['Вид должностного исполнения'][doct_ID] == 'Внешнее сов-во'):
            if (check_mo(doct_ID, location, filial, df_dir_main_doct, pilot) is True):
                df_test['Эксперт берем'] = 1
            else:
                df_test['Эксперт берем'] = 'МО'"""

        else:
            df_test['Эксперт берем'] = 1
        sphere = sphere + ".до экспертов"

    elif (str(df_test['Врач-эксперт']) != "nan"):
        data_exp = df_test['Дата визирования']
        i = df_pmu.loc[lambda x: x['Дата начала периода'] <= data_exp].loc[lambda x: x['Дата окончания периода'] >= data_exp].index
        start = str(df_oms['Дата начала периода'][i])[4:14]
        end = str(df_oms['Дата окончания периода'][i])[4:14]
        df_test['Неделя эксперты'] = start[8:10] + '.' + start[5:7] + '.' + start[0:4] + '-' +(
                                    end[8:10] + '.' + end[5:7] + '.' + end[0:4])
        df_test['Эксперт берем'] = 'Не в справ'
        sphere = sphere + ".до экспертов"
        data = df_test['Дата создания заключения'] 
    
    else:
        df_test['Эксперт берем'] = 'Нет эксп'


    doct_ID = df_test['Врач']
    
    if(doct_ID in list(df_dir_main_doct.index) and str(df_dir_main_doct['Место локации'][doct_ID]) != 'nan'):
        if (str(df_dir_main_doct['Место локации'][doct_ID]) == 'МРЦ'):
            reason = ['']
            if (check(data, doct_ID, location, df_date, df_dir_main_doct, filial, reason, pilot) is True):
                df_test['Врач берем'] = 1
                num = 1
                if (df_test['Наименование услуги'] == 'Рентгенография стопы с нагрузкой'):
                        num = 2
                try:
                    df[sphere][df_test['Врач']]+=num   #[df_test['Врач']] += 1
                    if (pay != 'ОМС'):
                        if (not df_dir_pmu_contracts.loc[lambda x: x['МО'] == location].empty):
                            do_pmu_contract.loc[df_test['Врач'], sphere]+=num
                        else:
                            do_pmu_no_contract.loc[df_test['Врач'], sphere]+=num
                    else:
                        do_oms.loc[df_test['Врач'], sphere]+=num
                except:
                    print(df_test['Врач'], sphere, pay)
                

            elif (reason[0] == 'Табель' and data == df_test['Дата визирования']):
                data = df_test['Дата создания заключения']
                if ((not df_date.loc[lambda x: x['ФИО'] == doct_ID].loc[lambda x: x['Дата'] == data].empty) 
                    or (not df_date.loc[lambda x: x['ФИО'] == doct_ID].loc[lambda x: x['Смена'] == 'Ночь'].loc[lambda x: x['Дата'] 
                    + datetime.timedelta(days=1) == data].empty)):
                    df_test['Врач берем'] = 1
                    num = 1
                    if (df_test['Наименование услуги'] == 'Рентгенография стопы с нагрузкой'):
                        num = 2   
                    df.loc[df_test['Врач'], sphere]+=num   #[df_test['Врач']] += 1
                    if (pay != 'ОМС'):
                        if (not df_dir_pmu_contracts.loc[lambda x: x['МО'] == location].empty):
                            do_pmu_contract.loc[df_test['Врач'], sphere]+=num
                        else:
                            do_pmu_no_contract.loc[df_test['Врач'], sphere]+=num
                    else:
                        do_oms.loc[df_test['Врач'], sphere]+=num
                else:
                    df_test['Врач берем'] = reason[0]
                
            else:
                df_test['Врач берем'] = reason[0]

            """elif (not df_dir_main_doct.loc[doct_ID].loc[lambda x: x['Вид занятости'] == 'внешний совместитель'].empty):
            if (check_mo(doct_ID, location, filial, df_dir_main_doct) is True):
                df_test['Врач берем'] = 1
            else:
                df_test['Врач берем'] = 'МО'"""   

        else:
            df_test['Врач берем'] = 1
            
    else:
        df_test['Врач берем'] = 'Нет в справ'
    i = df_pmu.loc[lambda x: x['Дата начала периода'] <= data].loc[lambda x: x['Дата окончания периода'] >= data].index
    start = str(df_oms['Дата начала периода'][i])[4:14]
    end = str(df_oms['Дата окончания периода'][i])[4:14]
    df_test['Неделя врачи'] = start[8:10] + '.' + start[5:7] + '.' + start[0:4] + '-' +(
        end[8:10] + '.' + end[5:7] + '.' + end[0:4])

    return(df_test)



"""input excel files"""
sheet_name = 'Анатомические области'
file_name = './выгрузки/2022.07.25_Справочники по МРЦ (1).xlsx'
df_dir_an_spheres = pd.read_excel(file_name, sheet_name=sheet_name, index_col=1)

sheet_name = 'Пилотные МО'
df_dir_MO = pd.read_excel(file_name, sheet_name=sheet_name, index_col=0)
sheet_name = 'Основной по врачам'
df_dir_main_doct = pd.read_excel(file_name, sheet_name=sheet_name, index_col=0)
print(df_dir_main_doct)
sheet_name = 'ДОП договора на оплату ПМУ'
df_dir_pmu_contracts = pd.read_excel(file_name, sheet_name=sheet_name, index_col=None)
sheet_name = 'АКТЦ'
df_dir_aktc = pd.read_excel(file_name, sheet_name=sheet_name, index_col=None)


file_name = './выгрузки/Выгрузка_15.07-24.07.xlsx'
sheet_name = 'Выгрузка 01.07-31.07'
df_test = pd.read_excel(file_name)
df_test['Врач берем'] = ""
df_test['Эксперт берем'] = ''
df_test['Тип услуги'] = ''
df_test['Неделя врачи'] = ''
df_test['Неделя эксперты'] = ''
df_test['Пилот'] = ''


file_name = './выгрузки/Доля_описаний_врачами_1 (3).xlsx'
sheet_name = 'Доля описаний'
df = pd.read_excel(file_name, sheet_name=sheet_name, index_col=0, header=0)
do_pmu_contract = pd.read_excel(file_name, sheet_name=sheet_name, index_col=0, header=0)
do_oms = pd.read_excel(file_name, sheet_name=sheet_name, index_col=0, header=0)
do_pmu_no_contract = pd.read_excel(file_name, sheet_name=sheet_name, index_col=0, header=0)


sheet_name = 'ОМС'
df_oms = pd.read_excel(file_name, sheet_name=sheet_name, index_col=0, header=0)


sheet_name = 'ПМУ'
df_pmu = pd.read_excel(file_name, sheet_name=sheet_name, index_col=0, header=0)


file_name = './выгрузки/табель по врачам с 25.06 по 24.07.xlsx'
sheet_name = 'Табель'
df_date = pd.read_excel(file_name, index_col=None, header=0)


"""main functions"""


df = df.applymap(lambda x: 0)
#df = df[df.index.duplicated()]
df_test = df_test.apply(count, axis = 1,result_type='expand', args= ( df_dir_MO, 
                df_dir_main_doct, df_dir_an_spheres, df, do_pmu_contract, 
                do_pmu_no_contract, do_oms, df_date, df_oms, df_pmu, df_dir_pmu_contracts, df_dir_aktc))


"""output to excel file"""


writer = pd.ExcelWriter('2022.07.27_Доля описаний врачами_ итог проги+с разделением_15.07.2022-24.07.2022.xlsx')
sheet_name = 'Доля описаний'
print(df)
print('Writing dolya opisaniy...\n')
df.to_excel(writer, sheet_name=sheet_name)
sheet_name = 'Доля описаний доп договора'
print('Writing dolya opisaniy PMU contract...\n')
do_pmu_contract.to_excel(writer, sheet_name=sheet_name)
sheet_name = 'Доля описаний с незакл договор'
print('Writing dolya opisaniy PMU no contract...\n')
do_pmu_no_contract.to_excel(writer, sheet_name=sheet_name)
sheet_name = 'Доля описаний ОМС'
print('Writing dolya opisaniy OMS...\n')
do_oms.to_excel(writer, sheet_name=sheet_name)
sheet_name = "Выгрузка берем"
print('Writing Берем/Не берем...\n')
df_test.to_excel(writer, sheet_name=sheet_name)

print('Saving...\n')
writer.save()
print("That's all. Bye!")
