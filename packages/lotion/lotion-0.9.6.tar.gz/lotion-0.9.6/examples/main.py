from datetime import date

from lotion import BasePage, Lotion, notion_database, notion_prop
from lotion.filter.builder import Builder
from lotion.filter.condition.cond import Cond
from lotion.properties import Date, MultiSelect, Number, Select, Title

# At first, you must create Lotion instance.
# You must set environment variable `NOTION_SECRET`.
lotion = Lotion.get_instance("NOTION_API_SECRET")

# You can simply use lotion like this.

pages = lotion.retrieve_database("1696567a3bbf803e9817c7ae1e398b71")
for page in pages:
    print(page.get_title().text)
    print(page.get_select("Category").selected_name)
    print("=====================================")

# If you want to use lotion with class-based API, you can use like this.


@notion_prop(name="Title")
class ExpenseTitle(Title):
    pass


@notion_prop(name="Date")
class ExpenseDate(Date):
    pass


@notion_prop(name="Category")
class ExpenseCategory(Select):
    pass


@notion_prop(name="Amount")
class Amount(Number):
    pass


@notion_prop(name="Payment")
class Payment(MultiSelect):
    pass


@notion_database(database_id="1696567a3bbf803e9817c7ae1e398b71")
class Expense(BasePage):
    expense_title: ExpenseTitle
    expense_date: ExpenseDate
    expense_category: ExpenseCategory
    amount: Amount
    payment: Payment


# Pattern1: Retrieve all pages

expenses = lotion.retrieve_pages(Expense)
for expense in expenses:
    print(expense.expense_title.text)
    print(expense.expense_date.date)
    print(expense.expense_category.selected_name)
    print(expense.amount.number)
    for payment in expense.payment.values:
        print(payment.name)
    print("=====================================")


# Pattern2: Retrieve pages with filter

## Pattern2-1: Retrieve pages with filter by simple condition
## You can use `search_pages` method to filter pages by a specific property.

category = ExpenseCategory.from_name("Transportation")
expenses = lotion.search_pages(Expense, [category])
for expense in expenses:
    print(expense.expense_title.text)
    print(expense.expense_date.date)
    print(expense.expense_category.selected_name)
    print(expense.amount.number)
    for payment in expense.payment.values:
        print(payment.name)

## Pattern2-2: Retrieve pages with filter by complex condition
## You can use `retrieve_pages` method to filter pages by multiple conditions.

filter_param = (
    Builder.create()
    .add(
        Amount.from_num(20),
        Cond.GREATER_THAN,
    )
    .add(Payment.from_name(["Credit Card"]), Cond.CONTAINS)
    .build()
)

expenses = lotion.retrieve_pages(Expense, filter_param)
for expense in expenses:
    print(expense.expense_title.text)
    print(expense.expense_date.date)
    print(expense.expense_category.selected_name)
    print(expense.amount.number)
    for payment in expense.payment.values:
        print(payment.name)

# Pattern3: Create/Update a page
# You can create a new page by using `create_page` method.
expense = Expense.create(
    [
        ExpenseTitle.from_plain_text("New Expense"),
        ExpenseDate.from_start_date(date(2025, 1, 4)),
        ExpenseCategory.from_name("Food"),
        Amount.from_num(20),
        Payment.from_name(["Credit Card"]),
    ]
)
created_page = lotion.create_page(expense)

# You can also update a page.

created_page.set_prop(ExpenseTitle.from_plain_text("Updated Name"))
created_page.set_prop(ExpenseCategory.from_name("Entertainment"))
lotion.update(created_page)
