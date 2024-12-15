import streamlit as st
from PyPDF2 import PdfReader
import re
import pandas as pd

st.set_page_config(
        page_title="ExpenseInsight",)

# Function to process the PDF and extract transactions from all pages
def process_pdf(file):
    # Read the PDF
    reader = PdfReader(file)
    all_data_rows = []
    previous_balance = None  # Track the balance across pages

    # Iterate over each page
    for page in reader.pages:
        # Extract text from the page
        raw_text = page.extract_text()

        # Normalize the text
        normalized_text = re.sub(r"\n(?!\d{2}-[A-Za-z]{3}-\d{4})", " ", raw_text)  # Merge multiline transactions
        normalized_text = re.sub(r"\s{2,}", " ", normalized_text)  # Remove extra spaces
        lines = normalized_text.split('\n')

        # Skip the first and last rows (header/footer)
        lines = lines[1:-1]

        # Extract relevant data rows
        for line in lines:
            # Check if the line starts with a date
            if re.match(r"^\d{2}-[A-Za-z]{3}-\d{4}", line):
                parts = line.split(' ')
                # First part is the Date
                date = parts[0]
                # Balance is always the last part
                balance = float(parts[-1].replace(',', ''))
                # Transaction amount is the second-to-last part
                transaction_amount = float(parts[-2].replace(',', ''))
                # Extract particulars
                particulars = ' '.join(parts[1:-2])

                # Determine transaction type (DR or CR)
                if "DR/" in line:  # Withdrawal
                    withdrawal = transaction_amount
                    deposit = 0.0
                elif "CR/" in line:  # Deposit
                    withdrawal = 0.0
                    deposit = transaction_amount
                else:
                    # Fallback to comparing balances (used if markers are absent)
                    if previous_balance is not None:
                        if balance < previous_balance:  # Balance decreased -> Withdrawal
                            withdrawal = transaction_amount
                            deposit = 0.0
                        else:  # Balance increased -> Deposit
                            withdrawal = 0.0
                            deposit = transaction_amount
                    else:
                        withdrawal, deposit = 0.0, 0.0

                # Update the previous balance
                previous_balance = balance

                # Append row to the data list
                all_data_rows.append([date, particulars, deposit, withdrawal, balance])

    # Create DataFrame
    columns = ['Date', 'Particulars', 'Deposits', 'Withdrawals', 'Balance']
    df = pd.DataFrame(all_data_rows, columns=columns)

    return df

# Streamlit App UI
st.title("ExpenseInsight")

# File upload
uploaded_file = st.file_uploader("Upload your IndusInd Bank Statement PDF", type="pdf")

if uploaded_file is not None:
    try:
        # Process the uploaded file
        with st.spinner("Processing..."):
            df = process_pdf(uploaded_file)
        
        # Display the DataFrame
        st.success("Processing Complete!")
        st.subheader("Extracted Transactions")
        st.dataframe(df)

        # Calculate and display the summary
        total_withdrawals = df['Withdrawals'].sum()
        total_deposits = df['Deposits'].sum()
        st.subheader("Summary")
        st.write(f"**Total Amount Spent (Withdrawals):** ₹{total_withdrawals:,.2f}")
        st.write(f"**Total Deposits:** ₹{total_deposits:,.2f}")

        # Option to download the DataFrame as CSV
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download as CSV",
            data=csv,
            file_name="transactions.csv",
            mime="text/csv",
        )
    except Exception as e:
        st.error(f"An error occurred: {e}")
