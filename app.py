import streamlit as st
import datetime
import pandas as pd
import os
import random
import matplotlib.pyplot as plt
import seaborn as sns
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import base64
import os
import pytz
import datetime
import pytz  # Make sure this is in requirements.txt

# Set your desired timezone (e.g., 'Asia/Kolkata' for India)
tz = pytz.timezone('Asia/Kolkata')  # Change this based on your location

# Get the current time in your timezone
current_time = datetime.datetime.now(tz)
today = current_time.date()



os.environ['TZ'] = 'Asia/Kolkata'  # Change to your timezone

class ExpenseTracker:
    def __init__(self):
        self.filepath = "expenses.csv"
        self.budget_file = "budget.csv"
        self.expenses = self.load_expenses()
        self.budget = self.load_budget()

        # Initialize session state for editing and refreshing
        if 'edit_expense' not in st.session_state:
            st.session_state.edit_expense = None
        if 'refresh' not in st.session_state:
            st.session_state.refresh = False

        self.run()

    def load_expenses(self):
        if os.path.exists(self.filepath):
            return pd.read_csv(self.filepath).values.tolist()
        return []

    def save_expenses(self):
        df = pd.DataFrame(self.expenses, columns=["Date", "Category", "Amount"])
        df.to_csv(self.filepath, index=False)

    def load_budget(self):
        if os.path.exists(self.budget_file):
            return pd.read_csv(self.budget_file, index_col=0).to_dict()["Budget"]
        return {}

    def save_budget(self):
        df = pd.DataFrame.from_dict(self.budget, orient='index', columns=["Budget"])
        df.to_csv(self.budget_file)

    def run(self):
        st.title("Smart Expense Tracker")

        menu = ["Add Expense", "View Expenses", "Set Budget", "Budget Summary", "Daily Expense", "Report"]
        choice = st.sidebar.selectbox("Menu", menu)

        if choice == "Add Expense":
            self.add_expense_ui()
        elif choice == "View Expenses":
            self.view_expenses()
        elif choice == "Set Budget":
            self.set_budget_ui()
        elif choice == "Budget Summary":
            self.budget_summary()
        elif choice == "Daily Expense":
            self.daily_expense()
        elif choice == "Report":
            self.generate_report()

        # Handle the refresh request
        if st.session_state.refresh:
            st.session_state.refresh = False
            st.rerun()

    def add_expense_ui(self):
        st.subheader("Add a New Expense")
        today = datetime.date.today()
        date = st.date_input("Date", today, max_value=today)

        categories = ["Food", "Transport", "Entertainment", "Shopping", "Bills"]
        category = st.selectbox("Category", categories)

        amount = st.text_input("Amount", "")

        if not amount.isdigit():
            st.error("Please enter a valid number for the amount.")
        else:
            amount = float(amount)

            if st.button("Add Expense"):
                self.add_expense(date, category, amount)

    def add_expense(self, date, category, amount):
        self.expenses.append([date.strftime('%Y-%m-%d'), category, amount])
        self.save_expenses()
        st.success(f"Expense Added: {date} | {category} | ${amount}")

    def set_budget_ui(self):
        st.subheader("Set Monthly Budget")

        today = datetime.datetime.now()
        available_months = [(today + datetime.timedelta(days=30 * i)).strftime('%Y-%m') for i in range(3)]

        selected_month = st.selectbox("Select Month", available_months)

        categories = ["Food", "Transport", "Entertainment", "Shopping", "Bills"]
        selected_category = st.selectbox("Select Category", categories)

        category_budget = st.text_input(f"Set Budget for {selected_category}", value="")

        if st.button("Set Budget"):
            try:
                budget_amount = float(category_budget)
                if budget_amount <= 0:
                    st.error("🚨 Error: Budget amount must be greater than zero.")
                    return

                self.budget[f"{selected_month}-{selected_category}"] = budget_amount
                self.save_budget()
                st.success(f"✅ Budget for {selected_category} in {selected_month} set to ${budget_amount:.2f}")
            except ValueError:
                st.error("🚨 Error: Please enter a valid number for the budget.")

        st.subheader(f"Budget Overview for {selected_month}")
        selected_view_month = st.selectbox("Select Month to View Budget", available_months, key="view_budget_month")

        # Fix: Ensure budget data is displayed
        filtered_budget = {k: v for k, v in self.budget.items() if k.startswith(selected_view_month)}

        if not filtered_budget:
            st.info("ℹ️ No budgets set for this month.")
            return

        budget_data = []
        for key, value in filtered_budget.items():
            category = key.split('-')[-1]  # Fix to get the last part as category
            spent = self.calculate_expense_for_category(selected_view_month, category)
            remaining = value - spent
            status = "✔️ Within Budget" if spent <= value else "❌ Over Budget"
            budget_data.append([category, f"${value:.2f}", f"${spent:.2f}", f"${remaining:.2f}", status])

        df_budget = pd.DataFrame(budget_data, columns=["Category", "Set Budget", "Used", "Remaining", "Status"])
        st.dataframe(df_budget, use_container_width=True)

        for row in budget_data:
            if row[4] == "❌ Over Budget":
                st.warning(f"⚠️ Warning: Your {row[0]} budget of ${row[1]} has been exceeded! You've spent ${row[2]}.")

    def calculate_expense_for_category(self, month, category):
        df = pd.DataFrame(self.expenses, columns=["Date", "Category", "Amount"])
        df["Date"] = pd.to_datetime(df["Date"])
        df["Month"] = df["Date"].dt.strftime('%Y-%m')

        filtered_df = df[(df["Month"] == month) & (df["Category"] == category)]
        return filtered_df["Amount"].sum() if not filtered_df.empty else 0.0

    # def view_expenses(self):
    #     st.subheader("View Expenses")
    #     if not self.expenses:
    #         st.write("No expenses recorded yet.")
    #         return

    #     # Create a DataFrame from expenses
    #     df = pd.DataFrame(self.expenses, columns=["Date", "Category", "Amount"])
    #     df["Date"] = pd.to_datetime(df["Date"])
    #     df["Year"] = df["Date"].dt.year
    #     df["Month"] = df["Date"].dt.strftime('%B')
    #     df["Original_Index"] = df.index  # Add original index for tracking

    #     # Year filter
    #     years = sorted(df["Year"].unique(), reverse=True)
    #     selected_year = st.selectbox("Select Year", ["All"] + years)

    #     if selected_year != "All":
    #         df = df[df["Year"] == selected_year]
    #         current_month = datetime.datetime.now().month
    #         available_months = [datetime.date(2000, m, 1).strftime('%B') for m in range(1, current_month + 1)]
    #     else:
    #         available_months = sorted(df["Month"].unique())

    #     # Month filter
    #     selected_month = st.selectbox("Select Month", ["All"] + available_months)

    #     # Category filter
    #     categories = sorted(df["Category"].unique())
    #     selected_category = st.selectbox("Select Category", ["All"] + categories)

    #     # Apply filters
    #     filtered_df = df.copy()
    #     if selected_month != "All":
    #         filtered_df = filtered_df[filtered_df["Month"] == selected_month]
    #     if selected_category != "All":
    #         filtered_df = filtered_df[filtered_df["Category"] == selected_category]

    #     # Calculate monthly and category totals for display
    #     # These values will be updated automatically when expenses are deleted
    #     total_month_expense = 0
    #     total_category_expense = 0

    #     # If a month is selected, calculate total for that month across all categories
    #     if selected_month != "All":
    #         month_df = df[df["Month"] == selected_month]
    #         total_month_expense = month_df["Amount"].sum()

    #     # If a category is selected, calculate total for that category across all months/years
    #     if selected_category != "All":
    #         category_df = df[df["Category"] == selected_category]
    #         total_category_expense = category_df["Amount"].sum()

    #     # Display the summary metrics at the top
    #     col1, col2 = st.columns(2)
    #     with col1:
    #         if selected_month != "All":
    #             st.metric(f"Total {selected_month} Expenses", f"${total_month_expense:.2f}")
    #         else:
    #             st.metric("Total All-Time Expenses", f"${df['Amount'].sum():.2f}")

    #     with col2:
    #         if selected_category != "All":
    #             st.metric(f"Total {selected_category} Expenses", f"${total_category_expense:.2f}")
    #         else:
    #             filtered_sum = filtered_df["Amount"].sum() if not filtered_df.empty else 0
    #             st.metric("Total for Current Filter", f"${filtered_sum:.2f}")

    #     # Display expenses with action buttons
    #     if not filtered_df.empty:
    #         st.write("### Expense List")

    #         # Check if we're in edit mode
    #         if st.session_state.edit_expense is not None:
    #             self.edit_expense_ui(st.session_state.edit_expense)

    #         # Display each expense with edit/delete buttons
    #         for i, row in filtered_df.iterrows():
    #             col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
    #             with col1:
    #                 st.write(f"**Date:** {row['Date'].strftime('%Y-%m-%d')}")
    #             with col2:
    #                 st.write(f"**Category:** {row['Category']}")
    #             with col3:
    #                 st.write(f"**${row['Amount']:.2f}**")
    #             with col4:
    #                 if st.button("Edit", key=f"edit_{row['Original_Index']}"):
    #                     st.session_state.edit_expense = int(row['Original_Index'])
    #                     st.session_state.refresh = True
    #                     st.rerun()
    #             with col5:
    #                 if st.button("Delete", key=f"delete_{row['Original_Index']}"):
    #                     self.delete_expense(int(row['Original_Index']))
    #                     st.session_state.refresh = True
    #                     st.rerun()
    #             st.divider()
    #     else:
    #         st.info("No expenses found for the selected filters.")
    def view_expenses(self):
        st.subheader("View Expenses")
        if not self.expenses:
            st.write("No expenses recorded yet.")
            return

        # Create DataFrame
        df = pd.DataFrame(self.expenses, columns=["Date", "Category", "Amount"])
        df["Date"] = pd.to_datetime(df["Date"])
        df["Year"] = df["Date"].dt.year
        df["Month"] = df["Date"].dt.strftime('%B')
        df["Original_Index"] = df.index  # Track original index

        # Year filter
        years = sorted(df["Year"].unique(), reverse=True)
        selected_year = st.selectbox("Select Year", ["All"] + years)

        if selected_year != "All":
            df = df[df["Year"] == selected_year]
            current_month = datetime.datetime.now().month
            available_months = [datetime.date(2000, m, 1).strftime('%B') for m in range(1, current_month + 1)]
        else:
            available_months = sorted(df["Month"].unique())

        # Month filter
        selected_month = st.selectbox("Select Month", ["All"] + available_months)

        # Category filter
        categories = sorted(df["Category"].unique())
        selected_category = st.selectbox("Select Category", ["All"] + categories)

        # Preserve the original DataFrame for calculations
        month_df = df[df["Month"] == selected_month] if selected_month != "All" else df
        total_month_expense = month_df["Amount"].sum()  # ✅ Total for selected month (ignoring category filter)

        # Apply both filters to get the filtered expenses
        filtered_df = month_df.copy()
        if selected_category != "All":
            filtered_df = filtered_df[filtered_df["Category"] == selected_category]

        # Calculate total category-wise expenses within the selected month
        if selected_category != "All" and selected_month != "All":
            total_category_expense = df[(df["Category"] == selected_category) & (df["Month"] == selected_month)]["Amount"].sum()
        else:
            total_category_expense = df[df["Category"] == selected_category]["Amount"].sum() if selected_category != "All" else 0

        # Total expenses across all time
        total_till_date = df["Amount"].sum()

        # Display Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Till Date", f"${total_till_date:.2f}")
        with col2:
            if selected_month != "All":
                st.metric(f"Total {selected_month} Expenses", f"${total_month_expense:.2f}")  # ✅ Month total ignores category
            else:
                st.metric("Total All-Time Expenses", f"${df['Amount'].sum():.2f}")
        with col3:
            if selected_category != "All":
                st.metric(f"Total {selected_category} Expenses", f"${total_category_expense:.2f}")  # ✅ Category total within month
            else:
                filtered_sum = filtered_df["Amount"].sum() if not filtered_df.empty else 0
                st.metric("Total for Current Filter", f"${filtered_sum:.2f}")

        # Display Expenses
        if not filtered_df.empty:
            st.write("### Expense List")

            # Check if we're in edit mode
            if st.session_state.edit_expense is not None:
                self.edit_expense_ui(st.session_state.edit_expense)

            # Display each expense
            for i, row in filtered_df.iterrows():
                col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])
                with col1:
                    st.write(f"**Date:** {row['Date'].strftime('%Y-%m-%d')}")
                with col2:
                    st.write(f"**Category:** {row['Category']}")
                with col3:
                    st.write(f"**${row['Amount']:.2f}**")
                with col4:
                    if st.button("Edit", key=f"edit_{row['Original_Index']}"):
                        st.session_state.edit_expense = int(row['Original_Index'])
                        st.session_state.refresh = True
                        st.rerun()
                with col5:
                    if st.button("Delete", key=f"delete_{row['Original_Index']}"):
                        self.delete_expense(int(row['Original_Index']))
                        st.session_state.refresh = True
                        st.rerun()
                st.divider()
        else:
            st.info("No expenses found for the selected filters.")


    def edit_expense_ui(self, index):
        st.write("### Edit Expense")

        # Get the expense to edit
        if index >= len(self.expenses):
            st.error("Expense not found. It may have been deleted.")
            st.session_state.edit_expense = None
            return

        expense = self.expenses[index]
        date_str, category, amount = expense

        # Convert date string to datetime
        date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()

        # Create form for editing
        with st.form(key=f"edit_form_{index}"):
            new_date = st.date_input("Date", date, max_value=datetime.date.today())

            categories = ["Food", "Transport", "Entertainment", "Shopping", "Bills"]
            new_category = st.selectbox("Category", categories, index=categories.index(category) if category in categories else 0)

            new_amount = st.number_input("Amount", value=float(amount), min_value=0.01, format="%.2f")

            col1, col2 = st.columns(2)
            with col1:
                update_button = st.form_submit_button("Update Expense")
            with col2:
                cancel_button = st.form_submit_button("Cancel")

        if update_button:
            # Update the expense
            self.expenses[index] = [new_date.strftime('%Y-%m-%d'), new_category, new_amount]
            self.save_expenses()
            st.success("✅ Expense updated successfully!")

            # Clear the edit state and refresh
            st.session_state.edit_expense = None
            st.session_state.refresh = True
            st.rerun()

        if cancel_button:
            # Clear the edit state and refresh
            st.session_state.edit_expense = None
            st.session_state.refresh = True
            st.rerun()

    def delete_expense(self, index):
        # Delete the expense at the given index
        if 0 <= index < len(self.expenses):
            expense = self.expenses[index]
            self.expenses.pop(index)
            self.save_expenses()
            return True
        return False

    def budget_summary(self):
        st.subheader("Budget Summary")

        # Motivational quotes for staying within budget
        positive_quotes = [
            "The art is not in making money, but in keeping it. - Proverb",
            "Beware of little expenses; a small leak will sink a great ship. - Benjamin Franklin",
            "Financial peace isn't the acquisition of stuff; it's learning to live on less than you make. - Dave Ramsey",
            "A budget is telling your money where to go instead of wondering where it went. - John C. Maxwell",
            "It's not your salary that makes you rich, it's your spending habits. - Charles A. Jaffe"
        ]

        # Financial advice for exceeding budget
        financial_advice = [
            "Try the 50/30/20 rule: 50% on needs, 30% on wants, and 20% on savings.",
            "Consider meal prepping to reduce food expenses.",
            "Use public transportation or carpooling to save on transport costs.",
            "Look for free entertainment options in your community.",
            "Create a shopping list and stick to it to avoid impulse purchases."
        ]

        # Financial challenges for gamification
        financial_challenges = [
            "No-spend challenge: Try not to spend any money for the next 3 days on non-essentials.",
            "Cash-only challenge: Use only cash for the next week to better track your spending.",
            "Pantry challenge: Use what you already have at home before buying more groceries.",
            "DIY challenge: Before buying something new, see if you can make it or fix it yourself.",
            "30-day saving challenge: Save a small, increasing amount each day for a month."
        ]

        # Get current month for default view
        current_month = datetime.datetime.now().strftime('%Y-%m')

        # Get all months with budget data
        all_budget_months = set()
        for key in self.budget.keys():
            month_parts = key.split('-')
            if len(month_parts) >= 2:  # Make sure there are at least 2 parts
                month = month_parts[0] + '-' + month_parts[1]
                all_budget_months.add(month)

        if not all_budget_months:
            st.info("No budget data available. Please set a budget first.")
            return

        # Convert to list and sort
        all_budget_months = sorted(list(all_budget_months))

        # Let user select month to view
        selected_month = st.selectbox("Select Month", all_budget_months, index=all_budget_months.index(current_month) if current_month in all_budget_months else 0)

        # Filter budget data for selected month
        filtered_budget = {k: v for k, v in self.budget.items() if k.startswith(selected_month)}

        if not filtered_budget:
            st.info(f"No budgets set for {selected_month}.")
            return

        # Get expense data
        df = pd.DataFrame(self.expenses, columns=["Date", "Category", "Amount"])
        df["Date"] = pd.to_datetime(df["Date"])
        df["Month"] = df["Date"].dt.strftime('%Y-%m')
        month_df = df[df["Month"] == selected_month]

        # Calculate total budget and spending
        total_budget = sum(filtered_budget.values())
        total_spent = month_df["Amount"].sum() if not month_df.empty else 0

        # Display overview
        st.markdown(f"## Monthly Overview for {selected_month}")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Budget", f"${total_budget:.2f}")
        with col2:
            st.metric("Total Spent", f"${total_spent:.2f}")
        with col3:
            remaining = total_budget - total_spent
            status = "✅ Under Budget" if remaining >= 0 else "❌ Over Budget"
            st.metric("Remaining", f"${remaining:.2f}", delta=f"{status}")

        # Display budget vs actual by category
        st.markdown("### Budget vs. Actual by Category")

        budget_data = []
        overall_status = "within"  # Default status

        for key, value in filtered_budget.items():
            parts = key.split('-')
            if len(parts) < 3:  # Check if key has enough parts
                st.error(f"Invalid budget key format: {key}")
                continue

            category = parts[-1]  # Get the last part as the category
            spent = month_df[month_df["Category"] == category]["Amount"].sum() if not month_df.empty else 0
            remaining = value - spent
            percentage = (spent / value * 100) if value > 0 else 0
            status = "✔️ Within Budget" if spent <= value else "❌ Over Budget"

            if spent > value:
                overall_status = "over"

            budget_data.append([
                category,
                f"${value:.2f}",
                f"${spent:.2f}",
                f"${remaining:.2f}",
                f"{percentage:.1f}%",
                status
            ])

        df_budget = pd.DataFrame(
            budget_data,
            columns=["Category", "Budget", "Spent", "Remaining", "Used (%)", "Status"]
        )
        st.dataframe(df_budget, use_container_width=True)

        # Check if this is a future month
        current_date = datetime.datetime.now()
        selected_date = datetime.datetime.strptime(selected_month, '%Y-%m')
        is_future_month = selected_date > current_date

        # Gamification and motivation section (only show for current or past months)
        if not is_future_month:
            st.markdown("### Financial Insights")

            if overall_status == "within":
                st.success("🎉 Congratulations! You're staying within your budget this month.")
                st.markdown("#### Your Financial Wisdom:")
                st.info(random.choice(positive_quotes))

                # Rewards for staying under budget
                st.markdown("#### 🏆 Your Reward")
                rewards = [
                    "Treat yourself to something small but meaningful that brings you joy.",
                    "Consider transferring some of your savings to an emergency fund or investment.",
                    "Share your success with someone close to you - celebrating wins helps build good habits!"
                ]
                st.markdown(f"✨ {random.choice(rewards)}")
            else:
                st.warning("⚠️ You've exceeded your budget in some categories.")
                st.markdown("#### Financial Tip:")
                st.info(random.choice(financial_advice))

                # Challenge for improvement
                st.markdown("#### 💪 Financial Challenge")
                st.markdown(f"🌟 {random.choice(financial_challenges)}")

            # Progress visualization
            st.markdown("### Your Budgeting Progress")

            # Calculate percentage of categories within budget
            categories_count = len(budget_data)
            within_budget_count = sum(1 for item in budget_data if "Within Budget" in item[5])
            progress_percentage = (within_budget_count / categories_count) * 100 if categories_count > 0 else 0

            # Display progress bar
            st.progress(progress_percentage / 100)
            st.write(f"You're on track with {within_budget_count} out of {categories_count} budget categories ({progress_percentage:.1f}%)")

            # Achievement system
            achievements = {
                "20": "Budget Beginner",
                "40": "Money Manager",
                "60": "Finance Apprentice",
                "80": "Budget Master",
                "100": "Financial Wizard"
            }

            current_achievement = None
            for threshold, title in sorted(achievements.items(), key=lambda x: int(x[0])):
                if progress_percentage >= int(threshold):
                    current_achievement = title

            if current_achievement:
                st.success(f"🏅 Current Achievement: {current_achievement}")
                next_level = None
                for threshold, title in sorted(achievements.items(), key=lambda x: int(x[0])):
                    if int(threshold) > progress_percentage:
                        next_level = (title, int(threshold))
                        break

                if next_level:
                    st.write(f"Next achievement: {next_level[0]} (at {next_level[1]}% completion)")
        else:
            # Message for future months
            st.info("📆 This is a future month. Financial insights and achievements will be available once expenses are recorded.")

    def daily_expense(self):
        st.subheader("Today's Expense")
        today = datetime.date.today().strftime('%Y-%m-%d')
        df = pd.DataFrame(self.expenses, columns=["Date", "Category", "Amount"])
        df = df[df["Date"] == today]

        if df.empty:
            st.write("No expenses recorded for today.")
        else:
            st.dataframe(df)
            total_expense_today = df["Amount"].sum()
            st.write(f"### Total Expense for Today: ${total_expense_today:.2f}")

    def generate_report(self):
        st.subheader("Expense Reports")

        # Create DataFrame from expenses
        if not self.expenses:
            st.warning("No expenses recorded yet. Please add some expenses to generate reports.")
            return

        df = pd.DataFrame(self.expenses, columns=["Date", "Category", "Amount"])
        df["Date"] = pd.to_datetime(df["Date"])
        df["Year"] = df["Date"].dt.year
        df["Month"] = df["Date"].dt.month
        df["Week"] = df["Date"].dt.isocalendar().week
        df["Month_Name"] = df["Date"].dt.strftime('%B')
        df["Day"] = df["Date"].dt.day

        # Report type selection
        report_type = st.radio(
            "Select Report Time Period",
            ["Yearly", "Monthly", "Weekly", "Daily"],
            horizontal=True
        )

        # Get data for filters
        years = sorted(df["Year"].unique(), reverse=True)
        months = sorted(df["Month"].unique())
        month_names = [datetime.date(2000, m, 1).strftime('%B') for m in months]

        # Initialize report data
        report_data = None
        report_title = ""
        period_name = ""

        if report_type == "Yearly":
            selected_year = st.selectbox("Select Year", years)
            period_name = str(selected_year)
            report_title = f"Yearly Expense Report - {selected_year}"
            report_data = df[df["Year"] == selected_year].copy()

        elif report_type == "Monthly":
            col1, col2 = st.columns(2)
            with col1:
                selected_year = st.selectbox("Select Year", years, key="monthly_year")
            with col2:
                current_month = datetime.datetime.now().month
                available_months = [datetime.date(2000, m, 1).strftime('%B') for m in range(1, current_month + 1)]
                selected_month = st.selectbox("Select Month", available_months, index=current_month - 1)

            period_name = f"{selected_month} {selected_year}"
            report_title = f"Monthly Expense Report - {selected_month} {selected_year}"

            # Convert month name to number
            month_num = datetime.datetime.strptime(selected_month, '%B').month
            report_data = df[(df["Year"] == selected_year) & (df["Month"] == month_num)].copy()

        elif report_type == "Weekly":
            col1, col2 = st.columns(2)
            with col1:
                selected_year = st.selectbox("Select Year", years, key="weekly_year")

            # Get available weeks for the selected year
            available_weeks = sorted(df[df["Year"] == selected_year]["Week"].unique())
            with col2:
                if not available_weeks:
                    st.warning(f"No expense data found for {selected_year}.")
                    return
                selected_week = st.selectbox("Select Week Number", available_weeks)

            week_start = df[(df["Year"] == selected_year) & (df["Week"] == selected_week)]["Date"].min()
            week_end = df[(df["Year"] == selected_year) & (df["Week"] == selected_week)]["Date"].max()

            period_name = f"Week {selected_week} ({week_start.strftime('%b %d')} - {week_end.strftime('%b %d')})"
            report_title = f"Weekly Expense Report - {period_name}"
            report_data = df[(df["Year"] == selected_year) & (df["Week"] == selected_week)].copy()

        elif report_type == "Daily":
            col1, col2, col3 = st.columns(3)
            with col1:
                selected_year = st.selectbox("Select Year", years, key="daily_year")
            with col2:
                current_month = datetime.datetime.now().month
                available_months = [datetime.date(2000, m, 1).strftime('%B') for m in range(1, current_month + 1)]
                selected_month = st.selectbox("Select Month", available_months, index=current_month - 1, key="daily_month")

            # Convert month name to month number directly
            try:
                month_num = datetime.datetime.strptime(selected_month, '%B').month

                # Get available days for the selected month and year
                filtered_df = df[(df["Year"] == selected_year) & (df["Month"] == month_num)]
                available_days = sorted(filtered_df["Day"].unique())

                if not available_days:
                    st.warning(f"No expenses found for {selected_month} {selected_year}.")
                    return

                with col3:
                    selected_date = st.date_input("Select Day", min_value=datetime.date(selected_year, month_num, 1), max_value=datetime.date.today())

                # Create date safely
                period_name = selected_date.strftime('%B %d, %Y')
                report_title = f"Daily Expense Report - {period_name}"
                report_data = df[df["Date"].dt.date == selected_date].copy()

            except (ValueError, IndexError) as e:
                st.error(f"Error processing date: {str(e)}")
                return

        if report_data is None or report_data.empty:
            st.warning(f"No expenses found for the selected {report_type.lower()} period.")
            return

        # Generate Report
        st.markdown(f"## {report_title}")

        # 1. Summary section
        st.markdown("### Summary")
        total_spent = report_data["Amount"].sum()
        categories = report_data["Category"].unique()
        num_transactions = len(report_data)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Spent", f"${total_spent:.2f}")
        with col2:
            st.metric("Categories", f"{len(categories)}")
        with col3:
            st.metric("Transactions", f"{num_transactions}")

        # 2. Category breakdown
        st.markdown("### Expense Breakdown by Category")
        category_summary = report_data.groupby("Category")["Amount"].sum().reset_index()
        category_summary["Percentage"] = (category_summary["Amount"] / total_spent * 100).round(1)
        category_summary = category_summary.sort_values("Amount", ascending=False)

        # Display as table
        st.dataframe(
            category_summary.rename(columns={"Amount": "Total ($)", "Percentage": "% of Spending"})
            .style.format({"Total ($)": "${:.2f}", "% of Spending": "{:.1f}%"}),
            use_container_width=True
        )

        # 3. Budget Comparison
        st.markdown("### Budget Analysis")

        col1, col2 = st.columns(2)

        # Category Pie Chart
        with col1:
            st.markdown("#### Spending by Category")
            fig, ax = plt.subplots(figsize=(8, 8))
            plt.pie(
                category_summary["Amount"],
                labels=category_summary["Category"],
                autopct='%1.1f%%',
                startangle=90,
                shadow=True
            )
            plt.axis('equal')
            st.pyplot(fig)

        # Budget comparison bar chart
        with col2:
            st.markdown("#### Budget vs. Actual")

            # Get budget data based on report period
            if report_type == "Monthly":
                # Use month_num directly
                if 'month_num' not in locals():
                    # Ensure month_num is defined in case we're not in the Daily section
                    month_num = datetime.datetime.strptime(selected_month, '%B').month

                budget_key_prefix = f"{selected_year}-{month_num:02d}"
                period_budget = {k.split('-')[-1]: v for k, v in self.budget.items() if k.startswith(budget_key_prefix)}

                if period_budget:
                    budget_data = []
                    for category in categories:
                        budget_amount = period_budget.get(category, 0)
                        actual_amount = category_summary[category_summary["Category"] == category]["Amount"].values[0]
                        budget_data.append([category, budget_amount, actual_amount])

                    budget_df = pd.DataFrame(budget_data, columns=["Category", "Budget", "Actual"])

                    fig, ax = plt.subplots(figsize=(8, 8))
                    x = range(len(budget_df))
                    width = 0.35

                    ax.bar([i - width/2 for i in x], budget_df["Budget"], width, label='Budget')
                    ax.bar([i + width/2 for i in x], budget_df["Actual"], width, label='Actual')

                    ax.set_xlabel('Category')
                    ax.set_ylabel('Amount ($)')
                    ax.set_title('Budget vs. Actual Spending')
                    ax.set_xticks(x)
                    ax.set_xticklabels(budget_df["Category"], rotation=45, ha="right")
                    ax.legend()

                    fig.tight_layout()
                    st.pyplot(fig)
                else:
                    st.info("No budget data available for this period.")
            else:
                st.info(f"Budget comparison is only available for monthly reports.")

        # 4. Spending Trends
        st.markdown("### Spending Trends")

        if report_type in ["Yearly", "Monthly"]:
            if report_type == "Yearly":
                # For yearly report, group by month
                trends_df = report_data.groupby(["Month_Name"])["Amount"].sum().reset_index()
                # Ensure proper month ordering
                month_order = {month: i for i, month in enumerate([
                    'January', 'February', 'March', 'April', 'May', 'June',
                    'July', 'August', 'September', 'October', 'November', 'December'
                ])}
                trends_df = trends_df.sort_values(by="Month_Name", key=lambda x: x.map(month_order))
                x_axis = "Month_Name"
                plt_title = f"Monthly Spending Trends for {selected_year}"
            else:
                # For monthly report, group by day
                trends_df = report_data.groupby(["Day"])["Amount"].sum().reset_index()
                trends_df = trends_df.sort_values("Day")
                x_axis = "Day"
                plt_title = f"Daily Spending Trends for {period_name}"

            fig, ax = plt.subplots(figsize=(10, 6))
            sns.lineplot(data=trends_df, x=x_axis, y="Amount", marker='o', linewidth=2, ax=ax)
            plt.title(plt_title)
            plt.ylabel("Amount ($)")
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.xticks(rotation=45)
            fig.tight_layout()
            st.pyplot(fig)

        elif report_type == "Weekly":
            # For weekly report, group by day of week
            report_data["DayOfWeek"] = report_data["Date"].dt.day_name()
            day_order = {day: i for i, day in enumerate([
                'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
            ])}
            trends_df = report_data.groupby(["DayOfWeek"])["Amount"].sum().reset_index()
            trends_df = trends_df.sort_values(by="DayOfWeek", key=lambda x: x.map(day_order))

            fig, ax = plt.subplots(figsize=(10, 6))
            sns.barplot(data=trends_df, x="DayOfWeek", y="Amount", ax=ax)
            plt.title(f"Spending Trend for {period_name}")
            plt.ylabel("Amount ($)")
            plt.xlabel("Day of Week")
            plt.tight_layout()
            st.pyplot(fig)

        # 5. Detailed Transactions
        st.markdown("### Detailed Transactions")
        detailed_df = report_data[["Date", "Category", "Amount"]].sort_values("Date", ascending=False)
        detailed_df["Date"] = detailed_df["Date"].dt.strftime('%Y-%m-%d')
        detailed_df = detailed_df.reset_index(drop=True)
        st.dataframe(detailed_df.rename(columns={"Amount": "Amount ($)"}), use_container_width=True)

        # 6. Download Report
        st.markdown("### Download Report")

        if st.button("Generate PDF Report"):
            pdf_buffer = self.create_pdf_report(report_title, period_name, report_data, category_summary, total_spent)

            # Create download link
            b64_pdf = base64.b64encode(pdf_buffer.getvalue()).decode()
            file_name = f"expense_report_{report_type.lower()}_{period_name.replace(' ', '_')}.pdf"
            href = f'<a href="data:application/pdf;base64,{b64_pdf}" download="{file_name}">Download PDF Report</a>'
            st.markdown(href, unsafe_allow_html=True)

    def create_pdf_report(self, report_title, period_name, report_data, category_summary, total_spent):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []

        # Define styles
        styles = getSampleStyleSheet()
        title_style = styles["Title"]
        heading_style = styles["Heading1"]
        normal_style = styles["Normal"]

        # Add title
        elements.append(Paragraph(report_title, title_style))
        elements.append(Spacer(1, 0.25*inch))

        # Add summary section
        elements.append(Paragraph("Expense Summary", heading_style))
        summary_text = f"""
        Period: {period_name}
        Total Spent: ${total_spent:.2f}
        Number of Transactions: {len(report_data)}
        Number of Categories: {len(report_data['Category'].unique())}
        """
        elements.append(Paragraph(summary_text, normal_style))
        elements.append(Spacer(1, 0.25*inch))

        # Category breakdown
        elements.append(Paragraph("Expense Breakdown by Category", heading_style))

        # Create category table
        category_data = [["Category", "Amount ($)", "Percentage (%)"]]
        for _, row in category_summary.iterrows():
            category_data.append([
                row["Category"],
                f"${row['Amount']:.2f}",
                f"{row['Percentage']:.1f}%"
            ])

        # Create the table
        table = Table(category_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)
        elements.append(Spacer(1, 0.25*inch))

        # Create category pie chart
        elements.append(Paragraph("Spending Distribution", heading_style))

        fig, ax = plt.subplots(figsize=(7, 7))
        plt.pie(
            category_summary["Amount"],
            labels=category_summary["Category"],
            autopct='%1.1f%%',
            startangle=90,
            shadow=True
        )
        plt.axis('equal')
        plt.title("Expense Distribution by Category")

        # Save plot to a temporary buffer
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png')
        img_buffer.seek(0)

        # Add the image to the PDF
        img = Image(img_buffer, width=6*inch, height=6*inch)
        elements.append(img)

        # Add detailed transactions
        elements.append(Paragraph("Detailed Transactions", heading_style))

        # Format transaction data
        transaction_data = [["Date", "Category", "Amount"]]
        sorted_data = report_data.sort_values("Date", ascending=False)
        for _, row in sorted_data.iterrows():
            transaction_data.append([
                row["Date"].strftime('%Y-%m-%d'),
                row["Category"],
                f"${row['Amount']:.2f}"
            ])

        # Create the transaction table
        trans_table = Table(transaction_data, colWidths=[1.5*inch, 2*inch, 1.5*inch])
        trans_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(trans_table)

        # Generate PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer

if __name__ == "__main__":
    ExpenseTracker()
