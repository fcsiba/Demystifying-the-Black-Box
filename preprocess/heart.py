import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)

def preprocess(dt):
    dt_example = pd.DataFrame(
        columns=['age', 'resting_blood_pressure', 'cholesterol', 'max_heart_rate_achieved', 'st_depression',
       'num_major_vessels', 'sex=male', 'chest_pain_type=atypical angina','chest_pain_type=non-anginal pain','chest_pain_type=typical angina','fasting_blood_sugar=lower than 120mg/ml','rest_ecg=left ventricular hypertrophy','rest_ecg=normal','exercise_induced_angina=yes','st_slope=flat','st_slope=upsloping','thalassemia=fixed defect','thalassemia=normal','thalassemia=reversable defect'])

    
    dt['chest_pain_type'][dt['chest_pain_type'] == 1] = 'typical angina'
    dt['chest_pain_type'][dt['chest_pain_type'] == 2] = 'atypical angina'
    dt['chest_pain_type'][dt['chest_pain_type'] == 3] = 'non-anginal pain'
    dt['chest_pain_type'][dt['chest_pain_type'] == 4] = 'asymptomatic'



    dt['rest_ecg'][dt['rest_ecg'] == 0] = 'normal'
    dt['rest_ecg'][dt['rest_ecg'] == 1] = 'ST-T wave abnormality'
    dt['rest_ecg'][dt['rest_ecg'] == 2] = 'left ventricular hypertrophy'



    dt['st_slope'][dt['st_slope'] == 1] = 'upsloping'
    dt['st_slope'][dt['st_slope'] == 2] = 'flat'
    dt['st_slope'][dt['st_slope'] == 3] = 'downsloping'

    dt['thalassemia'][dt['thalassemia'] == 1] = 'normal'
    dt['thalassemia'][dt['thalassemia'] == 2] = 'fixed defect'
    dt['thalassemia'][dt['thalassemia'] == 3] = 'reversable defect'

    lst = []
    for col in dt_example.columns:
        if col in dt.columns:
            lst.append(dt[col][0])
        elif dt[col.split('=')[0]][0] == col.split('=')[1]:
            lst.append(1)
        else:
             lst.append(0)
    dt_example.loc[0] = lst

    # for col in dt_example.columns:
    #     if col in dt.columns:
    #         dt_example[col][0] = dt[col][0]
    #     elif dt[col.split('=')][0] == col.split('=')[1]:
    #         dt_example[col][0] = 1
    #     else:
    #          dt_example[col][0] = 0

    df = dt_example
            
            

    from sklearn.preprocessing import StandardScaler
    sc_X = StandardScaler()
    X =  pd.DataFrame(sc_X.fit_transform(df,),
        columns=['age', 'resting_blood_pressure', 'cholesterol', 'max_heart_rate_achieved', 'st_depression',
       'num_major_vessels', 'sex_male', 'chest_pain_type_atypical angina','chest_pain_type_non-anginal pain','chest_pain_type_typical angina','fasting_blood_sugar_lower than 120mg/ml','rest_ecg_left ventricular hypertrophy','rest_ecg_normal','exercise_induced_angina_yes','st_slope_flat','st_slope_upsloping','thalassemia_fixed defect','thalassemia_normal','thalassemia_reversable defect'])

    return df








