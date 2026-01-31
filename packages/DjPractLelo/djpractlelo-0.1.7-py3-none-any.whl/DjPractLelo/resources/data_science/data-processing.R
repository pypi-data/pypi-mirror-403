data <- read.csv(
  "D:\\samruddhi\\MSC-Part-1\\Data Science Practs\\data-process.csv",
  stringsAsFactors = FALSE
)
cat("original data : ")
print(data)
# -----------------------------
# DATA CLEANING
# -----------------------------

# Replace missing Marks with mean
data$Marks[is.na(data$Marks)] <- mean(data$Marks, na.rm = TRUE)

# Replace missing Attendance with mean
data$Attendance[is.na(data$Attendance)] <- mean(data$Attendance, na.rm = TRUE)

# Replace empty Name values
data$Name[data$Name == ""] <- "Unknown"

# Replace empty Grade values
data$Grade[data$Grade == ""] <- "Not Assigned"

cat("\nAfter Data Cleaning:\n")
print(data)

# -----------------------------
# DATA TRANSFORMATION
# -----------------------------

# Add Pass/Fail column
data$Result <- ifelse(data$Marks >= 50, "Pass", "Fail")

# Normalize Marks
data$Normalized_Marks <- round(data$Marks / max(data$Marks), 2)

cat("\nAfter Data Transformation:\n")
print(data)

# -----------------------------
# DATA PREPARATION
# -----------------------------

# Sort data by Marks (Descending)
data <- data[order(-data$Marks), ]

# Select required columns
final_data <- data[, c("Student_ID", "Name", "Marks", "Attendance", "Result")]

cat("\nFinal Prepared Dataset:\n")
print(final_data)
