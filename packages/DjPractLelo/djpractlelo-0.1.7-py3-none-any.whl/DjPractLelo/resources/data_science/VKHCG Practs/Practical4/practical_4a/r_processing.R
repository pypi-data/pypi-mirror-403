# Read the CSV file
FileName = "c:/VKHCG/01-Vermeulen/00-RawData/IP_DATA_ALL.csv"
IP_DATA_ALL = read.csv(FileName, stringsAsFactors = FALSE)

# Fix column names by replacing spaces with dots
names(IP_DATA_ALL) = gsub(" ", ".", names(IP_DATA_ALL))

# Remove duplicate rows
IP_DATA_ALL_FIX = unique(IP_DATA_ALL)

# Print basic info about the dataset
cat("Rows:", nrow(IP_DATA_ALL_FIX), "Columns:", ncol(IP_DATA_ALL_FIX), "\n")

# Create a frequency table of countries
CountryFreq = as.data.frame(table(IP_DATA_ALL_FIX$Country))
names(CountryFreq) = c("Country", "Frequency")
View(CountryFreq)

# Calculate and print statistics for Latitude
cat("Latitude -> Min:", min(IP_DATA_ALL_FIX$Latitude, na.rm=TRUE),
    "Max:", max(IP_DATA_ALL_FIX$Latitude, na.rm=TRUE),
    "Mean:", mean(IP_DATA_ALL_FIX$Latitude, na.rm=TRUE),
    "Median:", median(IP_DATA_ALL_FIX$Latitude, na.rm=TRUE),
    "SD:", sd(IP_DATA_ALL_FIX$Latitude, na.rm=TRUE), "\n")

# Calculate and print statistics for Longitude
cat("Longitude -> Min:", min(IP_DATA_ALL_FIX$Longitude, na.rm=TRUE),
    "Max:", max(IP_DATA_ALL_FIX$Longitude, na.rm=TRUE),
    "Mean:", mean(IP_DATA_ALL_FIX$Longitude, na.rm=TRUE),
    "Median:", median(IP_DATA_ALL_FIX$Longitude, na.rm=TRUE),
    "SD:", sd(IP_DATA_ALL_FIX$Longitude, na.rm=TRUE), "\n")
