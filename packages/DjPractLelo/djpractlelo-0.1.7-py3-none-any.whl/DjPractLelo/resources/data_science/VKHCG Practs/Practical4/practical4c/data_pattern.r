FileName = "c:/VKHCG/01-Vermeulen/00-RawData/IP_DATA_ALL.csv"

IP_DATA_ALL = read.csv(FileName, stringsAsFactors = FALSE)

Country = unique(IP_DATA_ALL$Country)

Pattern = gsub("[^A-Za-z0-9 ]", "u",
          gsub("[0-9]", "N",
          gsub("[A-Za-z]", "A",
          gsub(" ", "b", Country))))

pattern_country = data.frame(Country = Country, Pattern = Pattern)

View(pattern_country)


