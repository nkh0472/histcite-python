def process_emails(df):
    """
    Iteratively find single CAU-Email pairs in the DataFrame.

    Parameters:
    - df: pandas DataFrame with columns 'CAU' and 'EM'

    Returns:
    - df: Updated DataFrame with 'CAU_u' and 'EM_u' columns reflecting processed data, contain uncertain CAUs and emails.
    - cau_email_dict: Dictionary containing the discovered CAU-Email pairs.
    """

    def remove_known_emails(row):
        """
        Helper function to remove known emails based on CAU and update CAU list.

        Parameters:
        - row: DataFrame row

        Returns:
        - Tuple of updated 'CAU_u' and 'EM_u'
        """
        cau_u = row["CAU_u"]
        em_u = row["EM_u"]

        if isinstance(cau_u, list):
            # Find CAUs in CAU_u that are already in the dictionary
            # known_caus_in_row = [cau for cau in cau_u if cau in known_caus] # vectorize
            known_caus_in_row = set(cau_u) & known_caus

            if known_caus_in_row:
                # Find known emails associated with known CAUs
                # for cau in known_caus_in_row: # vectorize
                #     known_emails = cau_email_dict[cau] # vectorize
                known_emails = set().union(
                    *(cau_email_dict[cau] for cau in known_caus_in_row)
                )

                # Remove known emails from 'EM_u'
                em_u = [email for email in em_u if email not in known_emails]

                # If any emails were removed, update CAU_u accordingly
                if len(em_u) < len(row["EM_u"]):
                    cau_u = [cau for cau in cau_u if cau not in known_caus_in_row]

        return cau_u, em_u

    def initialize_columns(df):
        """
        Helper function to initialize 'CAU_u' and 'EM_u' columns.

        Parameters:
        - df: DataFrame to initialize
        """
        df["CAU_u"] = df["CAU"]
        df["EM_u"] = df["EM"].apply(
            lambda x: set(re.split(r"[;,]\s*", str.strip(x))) if pd.notna(x) else set()
        )

    initialize_columns(df)

    cau_email_dict = {}
    new_pairs_found_set = set()

    while True:
        new_pairs_found_set.clear()

        for index, row in df.iterrows():
            if isinstance(row["CAU_u"], list) and len(row["CAU_u"]) == 1:
                cau = row["CAU_u"][0]

                if cau in cau_email_dict and row["EM_u"]:
                    cau_email_dict[cau] |= set(row["EM_u"])
                    df.at[index, "CAU_u"] = []
                    df.at[index, "EM_u"] = set()
                    new_pairs_found_set.add(cau)
                elif pd.notna(row["EM"]):
                    cau_email_dict[cau] = set(row["EM_u"])
                    df.at[index, "CAU_u"] = []
                    df.at[index, "EM_u"] = set()
                    new_pairs_found_set.add(cau)

        known_caus = set(cau_email_dict.keys())
        df[["CAU_u", "EM_u"]] = df.apply(
            remove_known_emails, axis=1, result_type="expand"
        )

        # Check if no new single CAU-Email pairs were found or 'CAU_u' is an empty list
        if (
            not new_pairs_found_set
            or df["CAU_u"]
            .apply(
                lambda x: not isinstance(x, list)
                or (isinstance(x, list) and all(e == "" for e in x))
            )
            .all()
        ):
            break

    print(f"Number of CAU-emails pair: {cau_email_dict}")
    return df, cau_email_dict
