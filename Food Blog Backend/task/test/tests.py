import sqlite3
from hstest import StageTest, CheckResult, WrongAnswer, dynamic_test, TestedProgram
import os


class SQLite3Test:
    """It's recommended to keep the sequence:
    1. Create object SQLite3Check
    2. Check is file exists
    3. Establish connection
    4. Check is table exists
    5. Check are columns exists
    6. Do the rest of tests on tables: is column primary key, not null

    To do tests: is unique and is foreign key"""

    cursor_message = f"There is no cursor to connection."  # Is it proper message?
    no_table_message = f"There is no table you are looking for."

    def __init__(self, file_name):  # file_name -> string
        self.file_name = file_name
        self.conn = None
        self.cursor = None

    def is_file_exist(self):
        if not os.path.exists(self.file_name):
            return f"The file '{self.file_name}' does not exist or is outside of the script directory."
        return False

    def connect(self):
        ans = self.is_file_exist()
        if ans:
            return ans
        try:
            self.conn = sqlite3.connect(self.file_name)
            self.cursor = self.conn.cursor()
        except sqlite3.OperationalError:
            raise WrongAnswer(f"DataBase {self.file_name} may be locked.")

    def close(self):
        try:
            self.conn.close()
        except AttributeError:
            raise WrongAnswer(self.cursor_message)

    def run_query(self, query):
        try:
            lines = self.cursor.execute(f"{query}")
        except AttributeError:
            raise WrongAnswer(self.cursor_message)
        except sqlite3.OperationalError:
            self.close()
            raise WrongAnswer(self.no_table_message)
        return lines

    def is_table_exist(self, name):  # table name -> string
        lines = self.run_query(
            f"SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{name}';").fetchall()
        if lines[0][0] == 0:
            self.close()
            raise WrongAnswer(f"There is no table named '{name}' in database {self.file_name}")

    def number_of_records(self, name, expected_lines):  # table name -> string, expected_lines -> integer
        lines = self.run_query(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        if lines != expected_lines:
            self.close()
            raise WrongAnswer(f"Wrong number of records in table {name}. Expected {expected_lines}, found {lines}")

    def is_column_exist(self, name,
                        names):  # table name -> string, column names -> list of strings for all columns, or list with one string for one column
        lines = self.run_query(f'select * from {name}').description
        if len(names) != 1:
            if sorted(names) != sorted([line[0] for line in lines]):
                self.close()
                raise WrongAnswer(
                    f"There is something wrong in table {name}. Found column names: {[line[0] for line in lines]}. Expected {names}'")
        else:
            if not any([names[0] == c_name for c_name in [line[0] for line in lines]]):
                self.close()
                raise WrongAnswer(
                    f"There is something wrong in table {name}. Found column names: {[line[0] for line in lines]}. Expected to find '{names[0]}'")

    def table_info(self, name, column,
                   attribute):  # table name -> string, column name -> string, attr ("PK" Primary Key; "NN" Not null)
        lines = self.run_query(f"PRAGMA table_info({name})").fetchall()
        if column not in [line[1] for line in lines]:
            raise WrongAnswer(f"There is no column {column}.")
        for line in lines:
            if attribute == "PK":
                if line[1] == column and line[5] != 1:
                    self.close()
                    raise WrongAnswer(f"There is no PRIMARY KEY parameter in {name} on column {column}.")
            elif attribute == "NN":
                if line[1] == column and line[3] != 1:
                    return CheckResult.wrong(f"There is no NOT NULL parameter in {name} on column {column}.")

    def is_unique(self, name, column):  # table name -> string, column name -> string
        lines = self.run_query(
            f"SELECT inf.name FROM pragma_index_list('{name}') as lst, pragma_index_info(lst.name) as inf WHERE lst.[unique] = 1;").fetchall()
        if not any([column in line for line in lines]):
            raise WrongAnswer(f"There is no UNIQUE parameter in {name} on column {column}.")
        return True

    def is_foreign_key(self, name, column):  # table name -> string, column name -> string
        lines = self.run_query(f"SELECT * FROM pragma_foreign_key_list('{name}');").fetchall()
        if not any([column in line for line in lines]):
            raise WrongAnswer(f"There is no FOREIGN KEY parameter in {name} on column {column}.")
        return True


data = [

    [["food_blog.db"]],
    [["food_blog.db", "--ingredients=milk,sugar", "--meals=breakfast"]],
    [["food_blog.db", "--ingredients=strawberry,sugar", "--meals=brunch,supper"]],
    [["food_blog.db", "--ingredients=cacao", "--meals=brunch,supper"]],  # Hot cacao, Hot cacao
    [["food_blog.db", "--ingredients=strawberry, cheese", "--meals=supper"]],
]


class FoodBlogStage1(StageTest):
    @dynamic_test(data=data)
    def test(self, arguments):

        if len(arguments) != 1:
            dbase = SQLite3Test(arguments[0])
            pr = TestedProgram()
            output = pr.start(arguments[0], arguments[1], arguments[2])

            if arguments[1] == "--ingredients=milk,sugar":
                if any(["Milkshake" not in output, "Hot cacao" not in output, "salad" in output]):
                    return CheckResult.wrong(f"Wrong answer. Found '{output}', expected Milkshake and Hot cacao.")
            elif arguments[1] == "--ingredients=strawberry,sugar":
                if any(["Milkshake" not in output, "Fruit salad" not in output, "cacao" in output]):
                    return CheckResult.wrong(f"Wrong answer. Found '{output}', expected Milkshake and Fruit salad.")
            elif arguments[1] == "--ingredients=cacao":
                if any([output.count("Hot cacao") != 2, "Milkshake" in output]):
                    return CheckResult.wrong(f"Wrong answer. Found '{output}', expected Hot cacao and Hot cacao.")
            else:
                if "no such recipes" not in output:
                    return CheckResult.wrong(f"Wrong answer. Found '{output}', expected 'no such recipes'.")
                if not dbase.is_file_exist():
                    try:
                        os.remove(arguments[0])
                    except:
                        return CheckResult.wrong("Looks like you didn't close connection with the database"
                                                 " at the end of the program!")

            if not pr.is_finished():
                return CheckResult.wrong("Your program unnecessarily waiting for input.")

        #  (table, (columns,), nr_of_records, (PK, ), ((NOT NULL, ), (not NOT NULL, )), ((FK, ), (not FK, )), ((UNIQUE, ), (not UNIQUE, )))
        else:
            test_data = (
                ("measures", ("measure_id", "measure_name"), 8, ("measure_id",), ((), ("measure_name",)), ((), ()),
                 (("measure_name",), ())),
                ("ingredients", ("ingredient_id", "ingredient_name"), 6, ("ingredient_id",), (("ingredient_name",), ()),
                 ((), ()), (("ingredient_name",), ())),
                ("meals", ("meal_id", "meal_name"), 4, ("meal_id",), (("meal_name",), ()), ((), ()),
                 (("meal_name",), ())),
                ("recipes", ("recipe_id", "recipe_name", "recipe_description"), 0, ("recipe_id",),
                 (("recipe_name",), ("recipe_description",)), ((), ()), ((), ("recipe_name", "recipe_description",))),
                ("serve", ("serve_id", "recipe_id", "meal_id"), 0, ("serve_id",), (("recipe_id", "meal_id"), ()),
                 (("recipe_id", "meal_id"), ()), ((), ())),
                ("quantity", ("quantity_id", "quantity", "recipe_id", "measure_id", "ingredient_id"), 0,
                 ("quantity_id",), (("quantity", "recipe_id", "measure_id", "ingredient_id"), ()),
                 (("recipe_id", "measure_id", "ingredient_id"), ()), ((), ())),
            )
            dbase = SQLite3Test(arguments[0])
            if not dbase.is_file_exist():
                try:
                    os.remove(arguments[0])
                except:
                    return CheckResult.wrong(
                        "Can't delete the database file! Make sure it is not used by other processes!")

            pr = TestedProgram()
            pr.start(arguments[0])

            dbase.connect()

            for table in test_data:

                dbase.is_table_exist(table[0])

                dbase.is_column_exist(table[0], table[1])

                dbase.number_of_records(table[0], table[2])

                for column in table[3]:
                    dbase.table_info(table[0], column, "PK")

                for column in table[4][0]:
                    ans = dbase.table_info(table[0], column, "NN")
                    if ans:
                        return ans

                for column in table[4][1]:
                    if not dbase.table_info(table[0], column, "NN"):
                        dbase.close()
                        return CheckResult.wrong(
                            f"Column {column} in table {table[0]} should not have Not Null attribute.")

                for column in table[5][0]:
                    dbase.is_foreign_key(table[0], column)

                for column in table[6][0]:
                    dbase.is_unique(table[0], column)

            for item in (
                    "Milkshake\nBlend all ingredients and put in the fridge.\n1 3 4\n500 ml milk\n1 cup strawberry\n1 tbsp sugar\n",
                    "\n",
                    "Hot cacao\nPour the ingredients into the hot milk. Mix it up.\n1 2\n250 ml milk\n2 tbsp cacao\n",
                    "\n",
                    "Hot cacao\nPour the ingredients into the hot milk. Mix it up.\n1 4\n250 ml milk\n2 tbsp cacao\n1 tsp sugar\n",
                    "\n",
                    "Fruit salad\nCut strawberries and mix with other fruits. you can sprinkle everything with sugar.\n3 4\n10 strawberry\n50 g black\n1 cup blue\n1 tsp sugar\n",
                    "\n",
                    "\n"):
                pr.execute(item)

            dbase.number_of_records("recipes", 4)
            dbase.number_of_records("serve", 9)
            dbase.number_of_records("quantity", 12)

            if not pr.is_finished():
                return CheckResult.wrong("Your program unnecessarily waiting for input.")

            dbase.close()
        return CheckResult.correct()


if __name__ == '__main__':
    FoodBlogStage1().run_tests()
