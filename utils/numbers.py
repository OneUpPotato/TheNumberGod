"""
Copyright 2020 OneUpPotato

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
from math import sqrt
from statistics import median

from praw.models import Redditor

from datetime import datetime

from typing import Union

from random import randint, choice
from sortedcontainers import SortedDict

from sympy.ntheory import isprime, primefactors

from utils.reddit import get_reddit
from utils.settings import get_settings


class Numbers:
    def __init__(self, reddit, settings) -> None:
        """
        This class deals with the key number handling.
        """
        self.reddit = reddit
        self.settings = settings

        # Define the numbers container (this is number to username).
        # This is also using an automatically sorted dictionary for efficiency.
        self.numbers = SortedDict({})

        # Load the numbers from Reddit.
        self.load_numbers()

        # Handle the current max number.
        self.current_max_number = 0
        self.set_max_number()

        # Load the subclasses.
        self.search = self.search(self)
        self.generation = self.generation(self)
        self.assignment = self.assignment(self)

        self.checks = NumberChecks()

    def load_numbers(self) -> None:
        """
        Loads the numbers from Reddit.
        """
        for flair in self.reddit.subreddit(self.settings.reddit.subreddit).flair(limit=None):
            try:
                number = int("".join([char for char in flair["flair_text"].lower().lstrip("#") if char.isnumeric() or char == "-"]))
                self.numbers[number] = flair["user"].name
            except Exception:
                pass
        print(f"Loaded {len(self.numbers)} numbers.")

    def set_max_number(self) -> None:
        """
        Sets the current max number based on the configuration.
        """
        if self.settings.reddit.assignment.numbers["static_max"] is False:
            numbers_assigned = len(list(self.numbers.keys()))
            self.current_max_number = numbers_assigned + len(self.settings.reddit.assignment.numbers["blacklist"]) + self.settings.reddit.assignment.numbers["max"]
        else:
            self.current_max_number = self.settings.reddit.assignment.numbers["max"]
        print(f"Set max number to {self.settings.reddit.assignment.numbers['max']}")

    class search:
        def __init__(self, parent) -> None:
            self.parent = parent

        def num_to_user(self, number) -> str:
            """
            Gets the username of the user who has a specific number (if any).
            :param number: The number to search for.
            :return: The user who has it or None.
            """
            try:
                return self.parent.numbers[number]
            except Exception:
                return None

        def user_to_num(self, username) -> int:
            """
            Gets the number of a specific user.
            :param username: The username to find the number of.
            :return: The number of that user (or None if they don't have one).
            """
            try:
                return int(list(self.parent.numbers.keys())[[user_with_number.lower() for user_with_number in self.parent.numbers.values()].index(username.lower())])
            except Exception:
                return None

    class generation:
        def __init__(self, parent) -> None:
            self.parent = parent

        def get_random_number(self) -> int:
            """
            Generates a randomly avaliable number.
            :return: The random number.
            """
            random_number = randint(self.parent.settings.reddit.assignment.numbers["min"], self.parent.current_max_number)
            if random_number in (list(self.parent.numbers.keys()) + self.parent.settings.reddit.assignment.blacklisted_numbers):
                return self.get_random_number()
            else:
                return random_number

        def get_random_user(self) -> tuple:
            """
            Gets a user with a number.
            :return: A random user and their number.
            """
            return choice(list(self.parent.numbers.items()))

    class assignment:
        def __init__(self, parent) -> None:
            self.parent = parent

        def assign_number(self, username: str, number: int = None) -> int:
            """
            Assign a number to a user.
            :param number: Optional. The number to assign the user.
            :return: The number assigned.
            """
            number = self.parent.generation.get_random_number() if number is None else number

            # Remove a previous number (if the user had one)
            old_number = self.parent.search.user_to_num(username)
            if old_number is not None:
                del self.parent.numbers[old_number]

            # Assign the user a flair.
            self.parent.reddit.subreddit(self.parent.settings.reddit.subreddit).flair.set(
                username,
                self.parent.settings.reddit.assignment.flair["text"].format(number),
                flair_template_id=(
                    self.parent.settings.reddit.assignment.flair["template_id"]
                    if self.parent.settings.reddit.assignment.flair["template_id"] else None
                ),
            )

            # Add the user to the numbers dictionary.
            self.parent.numbers[number] = username

            # Approve on the relevant subreddits.
            self.approve_number_subreddits(username, number)

            # Increase the max possible number.
            self.parent.current_max_number += 1

            # Print a success message.
            print(f"Succesfully set a user's number. (u/{username} as #{number})")

            return number

        def approve_number_subreddits(self, username: str, number: int) -> None:
            """
            Approves a user on all the subreddits relevant to their number.
            """
            subreddits = [f"NUM{get_number_nation(number)}"]
            if self.parent.checks.is_descendant_of_3(number):
                subreddits.append("descendantsof3")
            if self.parent.checks.is_seven_seas(number):
                subreddits.append("SevenSeasFaction")
            if self.parent.checks.is_prime_number(number):
                subreddits.append("the_primes")

            # Approve the user on the subreddits.
            for subreddit in subreddits:
                try:
                    self.parent.reddit.subreddit(subreddit).contributor.add(username)
                except Exception:
                    pass

    @property
    def statistics(self) -> dict:
        """
        Gets some statistics on the currently assigned numbers.
        :return: The calculated statistics.
        """
        number_list = self.parent.numbers.keys()
        stats = {
            "numbers_given": 0,  # Amount of Numbers Given
            "sum_of_numbers": 0,  # The sum of all the numbers.
            "lowest_positive": 0,  # The lowest positive number.
            "mean": 0,  # The mean of all the numbers.
            "median": 0,  # The median of all the numbers.
            "evens": 0,  # The amount of even numbers.
            "odds": 0,  # The amount of odd numbers.
            "below_500": 0,  # The amount of numbers below 500.
            "below_1000": 0,  # The amount of numbers below below 1000.
            "below_2500": 0,  # The amount of numbers below 2500.
        }

        # Find the lowest positive number.
        for number in number_list:
            if number >= 1:
                stats["lowest_positive"] = number
                break

        # Gather some statistics by looking through the numbers.
        for number in number_list:
            # Odd or Even
            if number % 2 == 0:
                stats["evens"] += 1
            else:
                stats["odds"] += 1

            # Below 500, 1000 or 2500
            if number <= 500:
                stats["below_500"] += 1
            if number <= 1000:
                stats["below_1000"] += 1
            if number <= 2500:
                stats["below_2500"] += 1

        # Work out these statistics.
        stats["numbers_given"] = len(number_list)
        stats["sum"] = sum(number_list)
        stats["mean"] = stats["sum"] / stats["numbers_given"]
        stats["median"] = median(number_list)

        # Switch these to percentages.
        stats["below_500"] = "{0:.2f}%".format(float((stats["below_500"] / stats["numbers_given"]) * 100))
        stats["below_1000"] = "{0:.2f}%".format(float((stats["below_1000"] / stats["numbers_given"]) * 100))
        stats["below_2500"] = "{0:.2f}%".format(float((stats["below_2500"] / stats["numbers_given"]) * 100))

        # Get the highest and lowest numbers.
        stats["highest"] = number_list[-1]
        stats["lowest"] = number_list[0]

        # Format these stats for the message.
        stats["highest_info"] = "#{number} (u/{username})".format(
            number=stats["highest"],
            username=self.search.num_to_user(stats["highest"]),
        )
        stats["lowest_positive_info"] = "#{number} (u/{username})".format(
            number=stats["lowest_positive"],
            username=self.search.num_to_user(stats["lowest_positive"]),
        )
        stats["lowest_info"] = "#{number} (u/{username})".format(
            number=stats["lowest"],
            username=self.search.num_to_user(stats["lowest"]),
        )

        return stats

    def __str__(self) -> str:
        return str(self.parent.numbers)

    def __repr__(self) -> SortedDict:
        return self.parent.numbers


class NumberChecks:
    def __init__(self) -> None:
        self.name_to_check = {
            "Lucky Club": self.is_lucky_club,
            "Seven Seas": self.is_seven_seas,
            "Deutopia": self.is_deutopia,
            "Unified Unities": self.is_unified_unities,
            "Bakery Club": self.is_bakery_club,
            "The Primes": self.is_prime_number,
            "Prime Pride": self.is_prime_number,
            "Semi-Prime": self.is_semi_prime_number,
            "Descendants of 3": self.is_descendant_of_3,
            "Tenplars": self.is_tenplar,
            "The Square Syndicate": self.is_square_number,
            "Millenium Club": self.is_millenium_club,
            "Palindromes": self.is_palindrome_number,
            "Sphenic Sphynxes": self.is_sphenic_number,
            "Negative": self.is_negative,
            "Otherwise Boring Numbers": self.is_obn,
        }

    def nation_and_countries(self, number: int) -> dict:
        """
        Gets a number's nation and countries.
        :param number: The number to check.
        :return: A dictionary containing the nation and their countr(y/ies).
        """
        result = {
            "nation": [],
            "countries": [],
        }

        # Get the number's nation.
        number_nation = get_number_nation(number)
        result["nation"] = [number_nation, f"r/{number_nation}"]

        # Get the number's countries.
        self.check_to_country = {
            self.is_descendant_of_3: ["Descendants of 3", "r/descendantsof3"],
            self.is_tenplar: ["Tenplars", "N/A"],
            self.is_unified_unities: ["(Unified Unities) Numbers with 1s", "N/A"],
            self.is_deutopia: ["(Deutopia) Numbers with 2s", "N/A"],
            self.is_seven_seas: ["(Seven Seas) Numbers with 7s", "r/SevenSeasFaction"],
            self.is_lucky_club: ["(Lucky Club) Numbers with 8s", "r/theluckyclub"],
            self.is_prime_number: ["Primes", "r/the_primes"],
            self.is_semi_prime_number: ["Semi Primes", "N/A"],
            self.is_palindrome_number: ["Palindromes", "N/A"],
            self.is_square_number: ["Square Numbers", "N/A"],
            self.is_sphenic_number: ["Sphenic Sphynxes", "N/A"],
            self.is_bakery_club: ["Bakery Club", "N/A"],
            self.is_negative: ["The Negatives", "N/A"],
        }
        for check, country_info in self.check_to_country.items():
            if check(number):
                result["countries"].append(country_info)

        if len(result["countries"]) == 0:
            result["countries"].append(["The Coalition of Otherwise Boring Numbers", "N/A"])

        return result

    def is_eligible_for(self, number: int, name: str) -> bool:
        """
        Checks if a number is eligible for a certain country/org of a specified name.
        :param number: The number to check eligibility for.
        :param name: The name of the group to check eligibility for.
        :return: Whether or not it is.
        """
        if name in self.name_to_check.keys():
            return self.name_to_check[name](number)
        return False

    def is_prime_number(self, number: int) -> bool:
        """
        Checks if a number is prime.
        :param number: The number to check.
        :return: Whether it is or not.
        """
        return isprime(number)

    def is_semi_prime_number(self, number: int) -> bool:
        """
        Checks if a number is semi prime. A semi prime number is the product of two prime numbers.
        :param number: The number to check.
        :return: Whether it is or not.
        """
        if number >= 1:
            prime_factors = list(primefactors(number))
            if len(prime_factors) == 2:
                if prime_factors[0] * prime_factors[1] == number:
                    return True
        return False

    def is_sphenic_number(self, number: int) -> bool:
        """
        Checks if a number is sphenic. A sphenic number is a number that is a positive number that is the product of three (different) prime numbers.
        :param number: The number to check.
        :return: Whether it is or not.
        """
        if number >= 1:
            prime_factors = list(primefactors(number))
            if len(prime_factors) == 3:
                if prime_factors[0] * prime_factors[1] * prime_factors[2] == number:
                    return True
        return False

    def is_palindrome_number(self, number: int) -> bool:
        """
        Checks if a number is palindromic (the same both backwards and normally).
        :param number: The number to check.
        :return: Whether it is or not.
        """
        if number >= 11:
            if str(number)[::-1] == str(number):
                return True
        return False

    def is_square_number(self, number: int) -> bool:
        """
        Checks if a number is square.
        :param number: The number to check.
        :return: Whether it is or not.
        """
        if int(sqrt(number) + 0.5) ** 2 == number:
            return True
        return False

    def is_bakery_club(self, number: int) -> bool:
        """
        Checks if a number is in the first 5000 decimal places of pi.
        :param number: The number to check.
        :return: Whether it is or not.
        """
        first_5000_dp_of_pi = "14159265358979323846264338327950288419716939937510582097494459230781640628620899862803482534211706798214808651328230664709384460955058223172535940812848111745028410270193852110555964462294895493038196442881097566593344612847564823378678316527120190914564856692346034861045432664821339360726024914127372458700660631558817488152092096282925409171536436789259036001133053054882046652138414695194151160943305727036575959195309218611738193261179310511854807446237996274956735188575272489122793818301194912983367336244065664308602139494639522473719070217986094370277053921717629317675238467481846766940513200056812714526356082778577134275778960917363717872146844090122495343014654958537105079227968925892354201995611212902196086403441815981362977477130996051870721134999999837297804995105973173281609631859502445945534690830264252230825334468503526193118817101000313783875288658753320838142061717766914730359825349042875546873115956286388235378759375195778185778053217122680661300192787661119590921642019893809525720106548586327886593615338182796823030195203530185296899577362259941389124972177528347913151557485724245415069595082953311686172785588907509838175463746493931925506040092770167113900984882401285836160356370766010471018194295559619894676783744944825537977472684710404753464620804668425906949129331367702898915210475216205696602405803815019351125338243003558764024749647326391419927260426992279678235478163600934172164121992458631503028618297455570674983850549458858692699569092721079750930295532116534498720275596023648066549911988183479775356636980742654252786255181841757467289097777279380008164706001614524919217321721477235014144197356854816136115735255213347574184946843852332390739414333454776241686251898356948556209921922218427255025425688767179049460165346680498862723279178608578438382796797668145410095388378636095068006422512520511739298489608412848862694560424196528502221066118630674427862203919494504712371378696095636437191728746776465757396241389086583264599581339047802759009946576407895126946839835259570982582262052248940772671947826848260147699090264013639443745530506820349625245174939965143142980919065925093722169646151570985838741059788595977297549893016175392846813826868386894277415599185592524595395943104997252468084598727364469584865383673622262609912460805124388439045124413654976278079771569143599770012961608944169486855584840635342207222582848864815845602850601684273945226746767889525213852254995466672782398645659611635488623057745649803559363456817432411251507606947945109659609402522887971089314566913686722874894056010150330861792868092087476091782493858900971490967598526136554978189312978482168299894872265880485756401427047755513237964145152374623436454285844479526586782105114135473573952311342716610213596953623144295248493718711014576540359027993440374200731057853906219838744780847848968332144571386875194350643021845319104848100537061468067491927819119793995206141966342875444064374512371819217999839101591956181467514269123974894090718649423196156794520809514655022523160388193014209376213785595663893778708303906979207734672218256259966150142150306803844773454920260541466592520149744285073251866600213243408819071048633173464965145390579626856100550810665879699816357473638405257145910289706414011097120628043903975951567715770042033786993600723055876317635942187312514712053292819182618612586732157919841484882916447060957527069572209175671167229109816909152801735067127485832228718352093539657251210835791513698820914442100675103346711031412671113699086585163983150197016515116851714376576183515565088490998985998238734552833163550764791853589322618548963213293308985706420467525907091548141654985946163718027098199430992448895757128289059232332609729971208443357326548938239119325974636673058360414281388303203824903758985243744170291327656180937734440307074692112019130203303801976211011004492932151608424448596376698389522868478312355265821314495768572624334418930396864262434107732269780280731891544110104468232527162010526522721116603966655730925471105578537634668206531098965269186205647693125705863566201855810072936065987648611791045334885034611365768675324944166803962657978771855608455296541266540853061434443185867697514566140680070023787765913440171274947042056223053899456131407112700040785473326993908145466464588079727082668306343285878569830523580893306575740679545716377525420211495576158140025012622859413021647155097925923099079654737612551765675135751782966645477917450112996148903046399471329621073404375189573596145890193897131117904297828564750320319869151402870808599048010941214722131794764777262241425485454033215718530614228813758504306332175182979866223717215916077166925474873898665494945011465406284336639379003976926567214638530673609657120918076383271664162748888007869256029022847210403172118608204190004229661711963779213375751149595015660496318629472654736425230817703675159067350235072835405670403867435136222247715891504953098444893330963408780769325993978054193414473774418426312986080998886874132604721"
        if str(number) in first_5000_dp_of_pi:
            return True
        return False

    def is_unified_unities(self, number: int) -> bool:
        """
        Checks if a number contains a 1.
        :param number: The number to check.
        :return: Whether it is or not.
        """
        if "1" in str(number):
            return True
        return False

    def is_deutopia(self, number: int) -> bool:
        """
        Checks if a number contains a 2.
        :param number: The number to check.
        :return: Whether it is or not.
        """
        if "2" in str(number):
            return True
        return False

    def is_seven_seas(self, number: int) -> bool:
        """
        Checks if a number contains a 7.
        :param number: The number to check.
        :return: Whether it is or not.
        """
        if "7" in str(number):
            return True
        return False

    def is_lucky_club(self, number: int) -> bool:
        """
        Checks if a number contains an 8.
        :param number: The number to check.
        :return: Whether it is or not.
        """
        if "8" in str(number):
            return True
        return False

    def is_descendant_of_3(self, number: int) -> bool:
        """
        Checks if a number is a multiple of 3.
        :param number: The number to check.
        :return: Whether it is or not.
        """
        if number % 3 == 0:
            return True
        return False

    def is_tenplar(self, number: int) -> bool:
        """
        Checks if a number is a multiple of 10.
        :param number: The number to check.
        :return: Whether it is or not.
        """
        if number % 10 == 0:
            return True
        return False

    def is_millenium_club(self, number: int) -> bool:
        """
        Checks if a number is in the 1000 to 1999 range.
        :param number: The number to check.
        :return: Whether it is or not.
        """
        if number >= 1000 and number <= 1999:
            return True
        return False

    def is_negative(self, number: int) -> bool:
        """
        Checks if a number is negative.
        :param number: The number to check.
        :return: Whether it is or not.
        """
        if number < 0:
            return True
        return False

    def parity(self, number: int) -> str:
        """
        Gets the parity of a number (odd or even).
        :param number: The number to check.
        :return: What parity the number is.
        """
        if number % 2 == 0:
            return "Even"
        return "Odd"

    def is_obn(self, number: int) -> bool:
        """
        Checks if a number is an otherwise boring number.
        :param number: The number to check.
        :return: Whether it is or not.
        """
        ignored_checks = [self.is_obn]
        for check in self.name_to_check.keys():
            if check not in ignored_checks:
                if check(number):
                    return False
        return True


def get_number_nation(number) -> str:
    """
    Gets the nation of a number.
    :param number: The number to get the nation from.
    :return: The number's nation.
    """
    return "000s" if len(str(number)) <= 2 else f"{str(number)[-3]}00s"


def is_allowed_number(user: Union[str, Redditor]) -> bool:
    """
    Checks if a user meets the requirements to be assigned a number.
    :param user: The user to check.
    :return: True or false depending on if they do.
    """
    redditor = user
    if isinstance(user, str):
        try:
            redditor = get_reddit().redditor(user)
        except Exception:
            return False

    # Ensure that the user meets the account age requirement.
    account_created = redditor.created_utc
    if (datetime.now().timestamp() - account_created) <= get_settings().reddit.assignment.requirements["account_age"]:
        return False

    # Ensure that the user meets the karma requirement.
    if (redditor.comment_karma + redditor.link_karma) < get_settings().reddit.assignment.requirements["karma"]:
        return False

    # The user meets the criteria to be assigned a number.
    return True
