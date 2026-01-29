# How to use Lotion

## Basic Usage

```python
from lotion import Lotion

# First, create a Lotion instance.
# Make sure to set the environment variable `NOTION_SECRET`.
lotion = Lotion.get_instance("NOTION_API_SECRET")

pages = lotion.retrieve_database("1696567a3bbf803e9817c7ae1e398b71")
for page in pages:
    print(page.get_title().text)
    print(page.get_select("Category").selected_name)
    print("=====================================")

page = lotion.retrieve_page("7c94bde2b57a4663ba612f85f63bf572")
```

## Using Custom Properties and Database Pages

If you prefer a class-based API, you can use Lotion as follows:

```python
from lotion import BasePage, notion_database, notion_prop
from lotion.properties import Date, MultiSelect, Number, Select, Title

@notion_prop(name="Title") # The name of the propety
class ExpenseTitle(Title):
    pass # You can implement additional methods


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
```

### Retrieve all pages

```python
expenses = lotion.retrieve_pages(Expense)
for expense in expenses:
    print(expense.expense_title.text)
    print(expense.expense_date.date)
    print(expense.expense_category.selected_name)
    print(expense.amount.number)
    for payment in expense.payment.values:
        print(payment.name)
    print("=====================================")
```

### Retrieve pages with filters

Retrieve pages with simple conditions using the `search_pages` method:

```python
category = ExpenseCategory.from_name("Transportation")
expenses = lotion.search_pages(Expense, [category])
for expense in expenses:
    print(expense.expense_title.text)
    print(expense.expense_date.date)
    print(expense.expense_category.selected_name)
    print(expense.amount.number)
    for payment in expense.payment.values:
        print(payment.name)
```

Use the `Builder` class and `retrieve_pages` method for complex conditions:

```python
filter_param = (
    Builder.create()
    .add(Amount.from_num(20), Cond.GREATER_THAN)
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
```

### Pattern3: Create/Update a page

You can create a new page by using `create_page` method, and update it by `update`.

```python
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

created_page.set_prop(ExpenseTitle.from_plain_text("Updated Name"))
created_page.set_prop(ExpenseCategory.from_name("Entertainment"))
lotion.update(created_page)
```


## About Property classes

You can read and update the following properties:

- Checkbox
- Date
- Email
- MultiSelect
- Number
- PhoneNumber
- Relation
- Select
- Status
- Text
- Title
- Url

You can only read (not update) the following properties:

- People
- Button
- Formula
- UniqueId
- Files
- Rollup
