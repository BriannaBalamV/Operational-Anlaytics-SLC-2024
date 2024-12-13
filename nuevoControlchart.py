######################################################
# Group: 3
# - Brianna Balam Velasco
# -Goutham Menon
######################################################

import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np


class Control_chart(): 
    def _get_labels_and_sample_size(self,data):
        observation_labels = []

        for col in data.columns:
            if col[0] =='x':
                observation_labels.append(col)
        return observation_labels,len(observation_labels)
    

    def _calculate_mean(self,data,kind,observation_labels): # mean and range for each sample 
        data['R']=np.NAN
        data['R']=data.loc[:,observation_labels].max(axis=1) - \
                        data.loc[:,observation_labels].min(axis=1)
        if kind == 'x_mean':
            data['x_mean']=data.loc[:,observation_labels].mean(axis=1) 
        
        return data,data['R'].mean()
    
    def _calculate_centre_line(self, data, kind):
        if kind == 'x_mean':
            return data['x_mean'].mean()
        if kind =='R':
            return data['R'].mean()
    
    def _calculate_control_limits(self,data,range_mean,sample_size,kind):
        factors_df = pd.read_csv('factors.csv')
        
        centre_line = self._calculate_centre_line(data=data,kind=kind) 
        A2 = factors_df.loc[factors_df['sample_size']==sample_size]['A2'].values[0]
        D4 = factors_df.loc[factors_df['sample_size']==sample_size]['D4'].values[0]
        D3 = factors_df.loc[factors_df['sample_size']==sample_size]['D3'].values[0]

        if kind =='R':
            return centre_line,D4*range_mean,D3*range_mean
                    # UCL        ,   LCL   RANGE 
        if kind =='x_mean':
            return centre_line, centre_line+A2*range_mean, centre_line-A2*range_mean

        # add more control limits for different control charts
    
    def _rule1_validator(self,ucl,lcl,data,kind):
        data['Rule 1']=np.NaN  # create a blank kind  
        for index,row in data.iterrows():  # find for observation outside control limits
            if row[kind] > ucl:   
                data.loc[index,['Rule 1']]=row[kind]
            elif row[kind] < lcl :  
                data.loc[index,['Rule 1']] =row[kind]
        return data
    
    ############################################################
    # TO-DO. Develop rule 2 validator as part of your project
    ############################################################
    
    ######################################################
    # Name:         Rule 2 Validator
    # Description:  Identifies points that violate Rule 2 (two out of three consecutive points outside 2-sigma limits).
    # Arguments:    centre_line: Center line of the control chart
    #               warning_limit_upper: Upper warning limit (2-sigma from the center line)
    #               warning_limit_lower: Lower warning limit (2-sigma from the center line)
    #               data: DataFrame with data points
    #               kind: Column name containing data points to be analyzed
    # Returns:      DataFrame with a new column ('Rule 2') indicating Rule 2 violations.
    ######################################################
    
    def _rule2_validator(self, centre_line, warning_limit_upper, warning_limit_lower, data, kind):
        """
        Rule 2: A process is assumed to be out of control if two out of three consecutive points 
        fall outside the 2-sigma warning limits on the same side of the center line.
        """
        data['Rule 2'] = np.NaN # create a blank column for Rule 2 violations
        for i in range(len(data) - 2): # iterate through the data points to identify Rule 2 violations 
            points = data[kind].iloc[i:i + 3] # get the three consecutive points to be analyzed for violations 
            count_above_warning = sum(points > warning_limit_upper) # count the number of points above the upper warning limit 
            count_below_warning = sum(points < warning_limit_lower) # count the number of points below the lower warning limit

            # mark the two out of three points if they exceed the warning limits on the same side
            if count_above_warning >= 2:
                data.loc[i:i + 2, 'Rule 2'] = points[points > warning_limit_upper]
            elif count_below_warning >= 2:
                data.loc[i:i + 2, 'Rule 2'] = points[points < warning_limit_lower]

        return data

    #############################################################    
    
    
    def _rule3_validator(self,centre_line,ucl,lcl,data,kind):
        data['Rule 3']=np.nan
        one_sd = max((ucl-centre_line) / 3,(centre_line-lcl) / 3)
        ucl_1sd = centre_line + one_sd 
        lcl_1sd = centre_line - one_sd
        for i in range(data.shape[0]):
            segment = data.loc[i:i+4][kind]
            try:
                if (segment > ucl_1sd).value_counts()[True] >=4:
                    data.loc[ (data.index >=i) & (data.index<=i+4) & ((data[kind]>ucl_1sd)),'Rule 3']=data[kind]  
            
            except:
                pass        
            try:
                if (segment < lcl_1sd).value_counts()[True] >=4:
                    data.loc[ (data.index >=i) & (data.index<=i+4) & (data[kind] < lcl_1sd),'Rule 3']=data[kind] 
            except:
                pass
        return data, ucl_1sd,lcl_1sd
    
    ############################################################
    # TO-DO. Develop rule 4 validator as part of your project
    ############################################################
    
    ######################################################
    # Name:         Rule 4 Validator
    # Description:  Identifies points that violate Rule 4 (nine or more consecutive points fall on one side of the center line).
    # Arguments:    centre_line: Center line of the control chart
    #               data: DataFrame with data points
    #               kind: Column name containing data points to be analyzed
    # Returns:      DataFrame with a new column ('Rule 4') indicating Rule 4 violations.
    ###################################################### 
    
    def _rule4_validator(self, centre_line, data, kind):
        """
        Rule 4: A process is assumed to be out of control if nine or more consecutive points fall to one side 
        of the center line.
        """
        data['Rule 4'] = np.NaN # create a blank column for Rule 4 violations
        consecutive_above = 0
        consecutive_below = 0
        for index, row in data.iterrows(): # iterate through the data points to identify Rule 4 violations
            point = row[kind]
            if point > centre_line: # check if the point is above the center line and increment the consecutive count accordingly
                consecutive_above += 1
                consecutive_below = 0
            elif point < centre_line: # check if the point is below the center line and increment the consecutive count accordingly
                consecutive_below += 1
                consecutive_above = 0
            else: # reset the consecutive counts if the point is on the center line
                consecutive_above = 0
                consecutive_below = 0

            # mark points if nine or more consecutive points fall on one side of the centre line
            if consecutive_above >= 9 or consecutive_below >= 9:
                data.loc[index-8:index, 'Rule 4'] = data[kind].iloc[index-8:index] 
        return data 
    ############################################################
    

    def _rule5_validator(self,data,kind):
        data['Rule 5']=np.nan
        current_check='increasing'
        i=1
        prev_value=np.NaN
        for index, row in data.iterrows():
            if index>0:
                if row[kind] > data.loc[index-1][kind]:
                    if current_check=='increasing':
                        i=i+1
                    else:
                        i=1
                    current_check='increasing'
                    
                elif row[kind] < data.loc[index-1][kind]:
                    if current_check=='decreasing':
                        i=i+1
                    else:
                        i=1
                    current_check='decreasing'
                else:
                    i=1
                if i>=5:
                        data.loc[index-i:index,'Rule 5']=data.loc[index-i:index][kind]
        return data
    
    
    

    def _create_chart(self,data, centre_line,ucl,lcl, kind,rules):
        g=sns.FacetGrid(data,height=6, aspect=3)  # Create a facegrid
        g=g.map(sns.lineplot,'sample_no',kind)  # Plot the data points 
        g.map(sns.scatterplot,'sample_no',kind) 
        plt.xticks(data['sample_no']) # set the x-axis ticks to the sample numbers 
        x1 = np.linspace(1,len(data)+1, 50) # create an array of 50 numbers starting from critical value and ending at 4
        y1 = np.linspace(lcl,lcl, 50) # create an array of 50 numbers starting from critical value and ending at 4
        y2 = np.linspace(ucl,ucl, 50) # create an array of 50 numbers starting from critical value and ending at 4
        
        plt.fill_between(x1,y1,y2,color='skyblue',alpha=0.25) # Fill 
        g.refline(y=centre_line,color='orange') # Plot the center line
        plt.annotate('CL',(len(data),centre_line+centre_line*0.009),size=15) # Annotate the center line
        g.refline(y=ucl,color='green') # Plot the UCL
        plt.annotate('UCL',(len(data),ucl+ucl*0.009),size=15)   # Annotate the UCL
        g.refline(y=lcl,color='green') # Plot the LCL
        plt.annotate('LCL',(len(data),lcl+lcl*0.009),size=15) # Annotate the LCL
        
        if 'Rule 1' in rules:
            data=self._rule1_validator(ucl,lcl,data,kind)
            g.map(sns.scatterplot,'sample_no','Rule 1',color='r',marker='>',s=100) #Plot Rule 1 
            ## https://matplotlib.org/stable/api/markers_api.html  for Markers 

        ## TO-DO 
        ##  Develop rule 2 as part of your project
        if 'Rule 2' in rules:
            sigma = (ucl - centre_line) / 3 # calculate the standard deviation (sigma) of the data points 
            warning_limit_upper = centre_line + 2 * sigma # calculate the upper warning limit (2-sigma from the center line)
            warning_limit_lower = centre_line - 2 * sigma # calculate the lower warning limit (2-sigma from the center line)
            data = self._rule2_validator(centre_line, warning_limit_upper, warning_limit_lower, data, kind) # identify Rule 2 violations 
            g.map(sns.scatterplot, 'sample_no', 'Rule 2', color='r', marker='o', s=80) # plot Rule 2 violations 
            g.refline(y=warning_limit_upper, color='grey', linestyle='--') # plot the upper warning limit 
            g.refline(y=warning_limit_lower, color='grey', linestyle='--')  
            
        #################################
        

        if 'Rule 3' in rules:
            data,ucl_1sd,lcl_1sd=self._rule3_validator(centre_line,ucl,lcl,data,kind)
        
            g.map(sns.scatterplot,'sample_no','Rule 3',color='r',marker='s',s=80) #Plot Rule 1
            g.refline(y=ucl_1sd, color='grey')
            g.refline(y=lcl_1sd, color='grey')

        ## TO-DO 
        ##  Develop rule 4 as part of your project
        if 'Rule 4' in rules:
            data = self._rule4_validator(centre_line, data, kind) # identify Rule 4 violations 
            g.map(sns.scatterplot, 'sample_no', 'Rule 4', color='r', marker='<', s=80) # plot Rule 4 violations 
            
        #################################

        if 'Rule 5' in rules:
            data = self._rule5_validator(data,kind)
            g.map(sns.scatterplot,'sample_no','Rule 5',color='r',marker='*',s=80) #Plot Rule 1

        g.add_legend()  
        return g 

    def plot_control_char(self,data,kind,rules=[]):
        observations_labels,n= self._get_labels_and_sample_size(data)
        data,range_mean = self._calculate_mean(data,kind,observations_labels)
        centre_line,ucl,lcl = self._calculate_control_limits(data,range_mean, n, kind)
        g=self._create_chart(data,centre_line,ucl,lcl,kind,rules)
        
        return g