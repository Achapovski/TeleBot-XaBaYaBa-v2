message-start = Hello { $username }, I am a bot that will help you keep track of your finances.
message-pre_settings = First, let's figure out what and how we will track.
                       Specify the monthly amount you would not like to exceed.
                       And a few more small settings :)
message-money_value = Enter the amount you would like to monitor for exceeding.
message-money_unlimited = (Enter "<u><b>0</b></u>" to disable threshold tracking.)
message-money_unlimited_select = Threshold value disabled.
message-confirm_money_value = Threshold value: <u><b>{ $money_value }</b> { $currency }</u>
message-lets_work = Now you can tell me the category name and the amount of money that needs to be recorded in this group:
                    Example:<b>

                        ➜ Food 10
                        ➜ Taxi 8.2
                        ➜ Miscellaneous 12.2</b>

                    Command /add - add a new category
                    Command /adds - create a super category
                    Command /as - add an alias for the category
                    Command /categories - display the list of categories

                    <u><i>Full functionality is available via the Reply-keyboard buttons</i></u>
message-working = Now you can tell me the category name and the amount of money that needs to be recorded in this group.

message-categories_list = Choose the category to which
                          you need to add an alias.
message-categories_choice = Selected category: <u><b><i>{ $category }</i></b></u>
message-categories_alias = Enter the desired alias for the category.
message-categories_alias_confirm = Set the alias <i><b><u>{ $alias }</u></b></i> for the category <i><b><u>{ $category }</u></b></i> ?

message-categories_menu_point = { $number }. { $category } - <b>{ $amount }</b> <b><i>{ $currency }</i></b>
message-money_indicator = Total/expected costs: <b><u>{ $total_money_value }/{ $expected_costs} <i>{ $money_currency}</i></u></b>

message-settings_menu = Settings options:
message-settings_delete = Delete category:

button-start = Let's start!
button-pre_settings = Go to settings
button-continue = Continue
button-confirm = Confirm
button-back = Back

button-currency = 💸
button-period = 📅
button-editor = ✏️

button-pagination_next = ➡️
button-pagination_back = ⬅️

button-day = Day
button-week = Week
button-month = Month
button-quarter = Quarter
button-half_year = Half year
button-year = Year

pre_setting_choice-currency = Choose the currency you want to track your finances in.
pre_setting_choice-language = You can change the language to:
pre_setting_choice-money_limit = Finally, set the monthly limit:
