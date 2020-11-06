def get_sdm_query(query,lambda_t=0.8,lambda_o=0.1,lambda_u=0.1):
        words = query.split()
        if len(words)==1:
            return f"#combine( {query} )"
        terms = " ".join(words)
        ordered = "".join([" #1({}) ".format(" ".join(bigram)) for bigram in zip(words,words[1:])])
        unordered = "".join([" #uw8({}) ".format(" ".join(bigram)) for bigram in zip(words,words[1:])])
        indri_query = f"#weight({lambda_t} #combine( {terms} ) {lambda_o} #combine({ordered}) {lambda_u} #combine({unordered}))"
        return indri_query


if __name__ == "__main__":
    query = "greta thunberg cross atlantic"
    print(get_sdm_query(query))
