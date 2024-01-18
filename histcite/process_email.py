def process_email_info(df):
    # get docs_df
    cau_email_dict = {}

    # Step 1: Find rows with only one CAU and save the corresponding email
    # Iterate through rows
    for index, row in df.iterrows():
        # Check if 'CAU' is a list with length 1 and 'EM' is not NaN
        if (
            isinstance(row["CAU"], list)
            and len(row["CAU"]) == 1
            and pd.notna(row["EM"])
        ):
            # Get the single CAU and corresponding email
            cau = row["CAU"][0]
            email = row["EM"]

            # Update cau_email_dict if cau already exists
            if cau in cau_email_dict:
                cau_email_dict[cau] += f", {email}"
            else:
                cau_email_dict[cau] = email

    # Step 2: Handle rows with multiple CAUs and emails
    df["CAU_u"] = df["CAU"]
    df["EM_u"] = df["EM"]
    for cau, email_entry in cau_email_dict.items():
        # Split the entry in 'EM' by ";", strip each email, and create a set for comparison
        known_emails = set(map(str.strip, re.split(r",\s*", email_entry)))

        # Remove known CAU-Email pairs from 'CAU_u' and 'EM_u'
        df["CAU_u"] = df["CAU_u"].apply(
            lambda x: [c for c in x if c != cau] if isinstance(x, list) else x
        )
        df["EM_u"] = df.apply(
            lambda row: "; ".join(
                [e for e in re.split(r";\s*", row["EM_u"]) if e not in known_emails]
            )
            if pd.notna(row["EM_u"])
            else np.nan,
            axis=1,
        )

    # Step 3: Find new CAU-Email pairs in 'CAU_u' and 'EM_u' and update the dictionary
    while True:
        # Iterate through rows
        new_pairs_found = False
        for index, row in df.iterrows():
            # Check if there are remaining CAUs in 'CAU_u'
            if isinstance(row["CAU_u"], list) and len(row["CAU_u"]) > 0:
                if len(row["CAU_u"]) == 1:
                    # Get the single CAU and corresponding email
                    cau = row["CAU_u"][0]

                    # Split the entry in 'EM_u' by ";", strip each email, and create a set for comparison
                    known_emails = set(
                        map(str.strip, re.split(r",\s*", str(row["EM_u"])))
                    )

                    # Check if any remaining email in 'EM_u'
                    remaining_emails = known_emails.copy()
                    if known_emails:
                        if "" in remaining_emails:
                            remaining_emails.remove("")
                    if remaining_emails:
                        email = remaining_emails.pop()
                        cau_email_dict[
                            cau
                        ] = f"{cau_email_dict.get(cau, '')}, {email}".lstrip(", ")
                        df.at[index, "CAU_u"] = np.nan
                        df.at[index, "EM_u"] = np.nan
                        new_pairs_found = True

        # Check if no new pairs were found or 'CAU_u' is an empty list
        if (
            not new_pairs_found
            or df["CAU_u"]
            .apply(
                lambda x: not isinstance(x, list)
                or (isinstance(x, list) and all(e == "" for e in x))
            )
            .all()
        ):
            break

    # return dict of CAU's email, and docs_df with uncertain CAU and email 
    return cau_email_dict, df