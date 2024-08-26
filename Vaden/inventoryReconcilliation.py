from flask import Flask, render_template, jsonify
import os
import pandas as pd

app = Flask(__name__)

def load_inventory(file_path):
    """Load inventory data from a CSV or Excel file."""
    _, file_extension = os.path.splitext(file_path)
    if file_extension.lower() == '.csv':
        return pd.read_csv(file_path)
    elif file_extension.lower() in ['.xls', '.xlsx']:
        return pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")

def extract_vins(df, vin_column_name):
    """Extract unique VINs from the specified column."""
    return df[vin_column_name].dropna().unique()

def compare_inventories(inventory_files, vin_column_names):
    """Compare VINs between inventories."""
    vin_data = {}
    inventory_data = {}
    for file_path, vin_column_name in zip(inventory_files, vin_column_names):
        file_name = os.path.basename(file_path)
        df = load_inventory(file_path)
        vin_numbers = extract_vins(df, vin_column_name)
        vin_data[file_name] = set(vin_numbers)
        inventory_data[file_name] = df

    all_vins = set.union(*vin_data.values())
    summary_df = pd.DataFrame(all_vins, columns=['VIN'])
    for file_name in vin_data:
        summary_df[file_name] = summary_df['VIN'].apply(lambda vin: vin in vin_data[file_name])

    return summary_df, vin_data, inventory_data

def generate_business_insights(inventory_data, vin_data, summary_df):
    """Generate various business insights based on the inventory data."""
    insights = {}

    # Total VINs and missing VINs
    total_vins = int(summary_df['VIN'].count())
    missing_in_vcp = int(summary_df[summary_df['VCP Factory Inventory.xlsx'] == False].shape[0])
    missing_in_cdk = int(summary_df[summary_df['CDK Inventory.xlsx'] == False].shape[0])
    insights['total_vins'] = total_vins
    insights['missing_in_vcp'] = missing_in_vcp
    insights['missing_in_cdk'] = missing_in_cdk

    # Example: Average Age Insights
    if 'Age (Days)' in inventory_data['VCP Factory Inventory.xlsx'].columns and 'TblAUinventory_Age' in inventory_data['CDK Inventory.xlsx'].columns:
        avg_age_vcp = inventory_data['VCP Factory Inventory.xlsx']['Age (Days)'].mean()
        avg_age_cdk = inventory_data['CDK Inventory.xlsx']['TblAUinventory_Age'].mean()
        insights['avg_age_vcp'] = avg_age_vcp
        insights['avg_age_cdk'] = avg_age_cdk
        insights['age_difference'] = avg_age_vcp - avg_age_cdk

    # Model Year Insights
    if 'Year' in inventory_data['VCP Factory Inventory.xlsx'].columns and 'TblAUinventory_Year' in inventory_data['CDK Inventory.xlsx'].columns:
        avg_model_year_vcp = inventory_data['VCP Factory Inventory.xlsx']['Year'].mean()
        avg_model_year_cdk = inventory_data['CDK Inventory.xlsx']['TblAUinventory_Year'].mean()
        model_year_distribution_vcp = inventory_data['VCP Factory Inventory.xlsx']['Year'].value_counts().to_dict()
        model_year_distribution_cdk = inventory_data['CDK Inventory.xlsx']['TblAUinventory_Year'].value_counts().to_dict()

        insights['avg_model_year_vcp'] = avg_model_year_vcp
        insights['avg_model_year_cdk'] = avg_model_year_cdk
        insights['model_year_distribution_vcp'] = model_year_distribution_vcp
        insights['model_year_distribution_cdk'] = model_year_distribution_cdk

    # Model Distribution Insights
    if 'Model' in inventory_data['VCP Factory Inventory.xlsx'].columns and 'TblAUinventory_Model' in inventory_data['CDK Inventory.xlsx'].columns:
        model_distribution_vcp = inventory_data['VCP Factory Inventory.xlsx']['Model'].value_counts().to_dict()
        model_distribution_cdk = inventory_data['CDK Inventory.xlsx']['TblAUinventory_Model'].value_counts().to_dict()

        insights['model_distribution_vcp'] = model_distribution_vcp
        insights['model_distribution_cdk'] = model_distribution_cdk

    return insights

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/compare_vins')
def compare_vins():
    try:
        vcp_factory_file = '/Users/nkhan/Documents/Vaden/Vaden/VCP Factory Inventory.xlsx'
        cdk_inventory_file = '/Users/nkhan/Documents/Vaden/Vaden/CDK Inventory.xlsx'

        inventory_files = [vcp_factory_file, cdk_inventory_file]
        vin_column_names = ['VIN', 'TblAUinventory_VIN']

        summary_df, vin_data, inventory_data = compare_inventories(inventory_files, vin_column_names)
        insights = generate_business_insights(inventory_data, vin_data, summary_df)

        vcp_not_in_cdk = vin_data[os.path.basename(vcp_factory_file)] - vin_data[os.path.basename(cdk_inventory_file)]
        cdk_not_in_vcp = vin_data[os.path.basename(cdk_inventory_file)] - vin_data[os.path.basename(vcp_factory_file)]

        return jsonify({
            'status': 'success',
            'summary': summary_df.to_dict(orient='records'),
            'vcp_not_in_cdk': list(vcp_not_in_cdk),
            'cdk_not_in_vcp': list(cdk_not_in_vcp),
            'insights': insights
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

if __name__ == '__main__':
    app.run(debug=True)
