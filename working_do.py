import pandas as pd
import datetime


def return_week(date):
    weekday = date.day_of_week
    start = date - pd.Timedelta(days = weekday)
    end = date + pd.Timedelta(days = 6 - weekday)
    
    if start.month != date.month:
        start = pd.Timestamp(date.year, date.month, 1)
    
    if end.month != date.month:
        end = end - pd.Timedelta(days = end.day)

    start = str(start)
    end = str(end)

    week = start[8:10] + '.' + start[5:7] + '.' + start[0:4] + '-' +(
                            end[8:10] + '.' + end[5:7] + '.' + end[0:4])
    
    return week


def return_modality(df_test, df_dir_an_spheres):
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


    elif(df_test['Модальность'] == 'ММГ' and df_test['Наименование услуги'] == 'Скрининг \
        рака молочной железы с помощью маммографии'):
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

    return sphere, sphere_s


def adding_to_report(pay, df_dir_pmu_contracts, location, do_pmu_contract, sphere,
                    df_test, do_pmu_no_contract, do_oms, df, num, strr):
    #strr == 'Врач' or strr == 'Врач-эксперт'
    try:
        df[sphere][df_test[strr]]+=num   #[df_test['Врач']] += 1
        if (pay != 'ОМС'):
            if (not df_dir_pmu_contracts.loc[lambda x: x['МО'] == location].empty):
                do_pmu_contract.loc[df_test[strr], sphere]+=num
            else:
                do_pmu_no_contract.loc[df_test[strr], sphere]+=num
        else:
            do_oms.loc[df_test[strr], sphere]+=num
    except:
        print(df_test[strr], sphere, pay)
    return df


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
        pilot[0] = 'АКТЦ'
    return


def check_tabel(data, doct_ID, df_date):
    return ((not df_date.loc[lambda x: x['ФИО'] == doct_ID].loc[lambda x: x['Дата'] == data].empty) 
            or (not df_date.loc[lambda x: x['ФИО'] == doct_ID].loc[lambda x: x['Смена'] == 'Ночь'].loc[lambda x: x['Дата'] 
            + datetime.timedelta(days=1) == data].empty))


def check(data, doct_ID, location, df_date, df_dir_main_doct, filial, reason, pilot):

    i = 0
    if (df_dir_main_doct['Дата начала работы'][doct_ID] <= data):
        
        if check_tabel(data, doct_ID, df_date):
            
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


def check_doct(data, doct_ID, location, df_date, df_dir_main_doct, filial, reason, pilot, df_test):
    bool_check = check(data, doct_ID, location, df_date, df_dir_main_doct, filial, reason, pilot)
    
    if not bool_check and reason[0] == 'Табель' and data == df_test['Дата визирования']:
        data = df_test['Дата создания заключения']
        bool_check = check_tabel(data, doct_ID, df_date)

    
    return bool_check


def count(df_test,  df_dir_MO, df_dir_main_doct, df_dir_an_spheres, df, do_pmu_contract, 
        do_pmu_no_contract, do_oms, df_date, df_dir_pmu_contracts, df_dir_aktc):
    if (str(df_test['Дата визирования']) == 'NaT'):
        df_test['Дата визирования'] = df_test['Дата создания заключения']
    if (df_test['Дата визирования'] < df_test['Дата создания заключения']):
        df_test['Дата визирования'], df_test['Дата создания заключения'] =\
             df_test['Дата создания заключения'], df_test['Дата визирования']

    pay = df_test['Тип оплаты окончательный']
    data = df_test['Дата визирования']
    location = df_test['МО']
    filial = df_test['Филиал']
    pilot = ['Внепилот']
    aktc = ['Не АКТЦ']

    sphere, sphere_s = return_modality(df_test, df_dir_an_spheres)
    check_pilot(df_dir_MO, location, pilot)
    #check_aktc(df_dir_aktc, location, aktc, filial)
    
    df_test['Пилот'] = pilot[0]
    #df_test['АКТЦ'] = aktc[0]
    df_test['Тип услуги'] = sphere_s
    reason = ['']
    
    if (str(df_test['Врач-эксперт']) != "nan"):
        data_exp = df_test['Дата визирования']
        data = df_test['Дата создания заключения']
        sphere = sphere + ".до экспертов"
        doct_ID = df_test['Врач-эксперт']
        df_test['Эксперт берем'] = 'Не в справ' 
        df_test['Неделя эксперты'] = return_week(data_exp)
        sphere_exp = sphere + ".эксперты"
        try:
            n = df_dir_main_doct['Место локации'][df_test['Врач-эксперт']]
        except:
            print(df_test['Врач-эксперт'], "эксп")
            return df_test
        if (str(df_dir_main_doct['Место локации'][df_test['Врач-эксперт']]) != 'nan'):
            df_test['Эксперт берем'] = 1
            
            if (str(df_dir_main_doct['Место локации'][doct_ID]) == 'МРЦ'):
                
                if (check(data_exp, doct_ID, location, df_date, df_dir_main_doct, filial, reason, pilot) is True):
                    
                    if(sphere == 'ФЛГ'): 
                        df = adding_to_report(pay, df_dir_pmu_contracts, location, do_pmu_contract, sphere_exp,
                        df_test, do_pmu_no_contract, do_oms, df, 1, 'Врач-эксперт')

                else:
                    df_test['Эксперт берем'] = reason[0]
     
    else:
        df_test['Эксперт берем'] = 'Нет эксп'

    doct_ID = df_test['Врач']
    try:
        n = df_dir_main_doct['Место локации'][doct_ID]
    except:
        print(doct_ID, "врач")
        return df_test
    if(doct_ID in list(df_dir_main_doct.index) and str(df_dir_main_doct['Место локации'][doct_ID]) != 'nan'):
        df_test['Врач берем'] = 1
        
        if (str(df_dir_main_doct['Место локации'][doct_ID]) == 'МРЦ'):
            num = 1
            
            if (df_test['Наименование услуги'] == 'Рентгенография стопы с нагрузкой'):  num = 2
            
            if (check_doct(data, doct_ID, location, df_date, df_dir_main_doct, filial, reason, pilot, df_test) is True):
                df = adding_to_report(pay, df_dir_pmu_contracts, location, do_pmu_contract, sphere,
                                        df_test, do_pmu_no_contract, do_oms, df, num, 'Врач')
                
            else:
                df_test['Врач берем'] = reason[0]
       
    else:
        df_test['Врач берем'] = 'Нет в справ'

    df_test['modality'] = sphere
    try:
        df_test['Неделя врачи'] = return_week(data)
    except:
        print(data, str(data), type(data))
        data = df_test['Дата создания заключения']
        df_test['Неделя врачи'] = return_week(data)
    return(df_test)


def input_excel_files():
    file_name = './выгрузки/2022.10.12_Справочники по МРЦ.xlsx'

    sheet_name = 'Анатомические области'
    df_dir_an_spheres = pd.read_excel(file_name, sheet_name=sheet_name, index_col=1)

    sheet_name = 'Пилотные МО'
    df_dir_MO = pd.read_excel(file_name, sheet_name=sheet_name, index_col=0)

    sheet_name = 'Основной по врачам'
    df_dir_main_doct = pd.read_excel(file_name, sheet_name=sheet_name, index_col=None)
    df_dir_main_doct['ФИО врача'] = df_dir_main_doct['ФИО врача'].str.title()
    df_dir_main_doct = df_dir_main_doct.set_index('ФИО врача')
    print(df_dir_main_doct)

    sheet_name = 'ДОП договора на оплату ПМУ'
    df_dir_pmu_contracts = pd.read_excel(file_name, sheet_name=sheet_name, index_col=None)

    sheet_name = 'АКТЦ'
    df_dir_aktc = pd.read_excel(file_name, sheet_name=sheet_name, index_col=None)


    file_name = './выгрузки/CONCL_DAY_12102022(1).xlsx'
    df_test = pd.read_excel(file_name)

    df_test['Неделя врачи'], df_test['Тип услуги'], df_test['Врач берем'] = "", "", ""
    df_test['modality'], df_test['Пилот'], df_test['Неделя эксперты'] = "", "", ""
    df_test['Эксперт берем'] = ""
    df_test['Врач'] = df_test['Врач'].str.title()
    df_test['Врач-эксперт'] = df_test['Врач-эксперт'].str.title()



    file_name = './выгрузки/Табель врачей 11.10.22 (1).xlsx'

    sheet_name = 'Табель'
    df_date = pd.read_excel(file_name, index_col=None, header=0)
    df_date['ФИО'] = df_date['ФИО'].str.title()
    return df_dir_an_spheres, df_dir_MO, df_dir_main_doct, df_dir_pmu_contracts, df_dir_aktc, df_test, df_date


def create_dataframes_for_writing_result(df_dir_main_doct):
    ind = df_dir_main_doct.loc[df_dir_main_doct['Место локации'] == 'МРЦ'].index
    col = ["Денс",	"КТ 1 зона",	"КТ 2 и более зон",	"КТ с КУ 1 зона",	"КТ с КУ 2 и более зон",
        "ММГ",	"СРМЖ",	"МРТ",	"МРТ с КУ 1 зона",	"МРТ с КУ 2 и более зон",	"РГ",	"ФЛГ",
            "Денс.до экспертов",	"КТ 1 зона.до экспертов",	"КТ 2 и более зон.до экспертов",
                "КТ с КУ 1 зона.до экспертов",	"КТ с КУ 2 и более зон.до экспертов",	"ММГ.до экспертов",
                    "СРМЖ.до экспертов",	"МРТ.до экспертов",	"МРТ с КУ 1 зона.до экспертов",
                        "МРТ с КУ 2 и более зон.до экспертов",	"РГ.до экспертов",	"ФЛГ.до экспертов",	"ФЛГ.эксперты"]


    df = pd.DataFrame(index = ind, columns=col)
    do_pmu_contract = pd.DataFrame(index = ind, columns=col)
    do_oms = pd.DataFrame(index = ind, columns=col)
    do_pmu_no_contract = pd.DataFrame(index = ind, columns=col)
    df = df.applymap(lambda x: 0)
    do_pmu_contract = do_pmu_contract.applymap(lambda x: 0)
    do_oms = do_oms.applymap(lambda x: 0)
    do_pmu_no_contract = do_pmu_no_contract.applymap(lambda x: 0)
    return df, do_oms, do_pmu_contract, do_pmu_no_contract


def output_to_excel_file(df, do_pmu_contract, do_pmu_no_contract, do_oms, df_test):
    writer = pd.ExcelWriter('./results/2022.10.12_Доля описаний врачами_итог проги+с разделением_11.10.2022-11.10.2022.xlsx')
    #writer = pd.ExcelWriter('./results/2022.10.06_test.xlsx')

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


def main():
    df_dir_an_spheres, df_dir_MO, df_dir_main_doct, df_dir_pmu_contracts\
        , df_dir_aktc, df_test, df_date = input_excel_files()
    
    df, do_oms, do_pmu_contract, do_pmu_no_contract =\
         create_dataframes_for_writing_result(df_dir_main_doct)

    df_test = df_test.apply(count, axis = 1,result_type='expand', args= ( df_dir_MO, 
                    df_dir_main_doct, df_dir_an_spheres, df, do_pmu_contract, 
                    do_pmu_no_contract, do_oms, df_date, df_dir_pmu_contracts, df_dir_aktc))
    

    output_to_excel_file(df, do_pmu_contract, do_pmu_no_contract, do_oms, df_test)
    
    print("That's all. Bye!")


main()