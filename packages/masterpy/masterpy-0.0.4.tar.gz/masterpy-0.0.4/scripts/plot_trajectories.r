#!/usr/bin/env Rscript

# Load the rjson library to handle JSON data
library(rjson)

# Fetch command-line arguments, specifically the filename
args = commandArgs(trailingOnly = T)

# Read in the JSON file provided as the first command-line argument
data <- fromJSON(file=args[1])
out_file <- args[2]
if (length(data$trajectories) == 1) {
  data$trajectories = data$trajectories[[1]]
}else{
  data$trajectories = data[-which(names(data) == "sim")]
}

# Define a function to compute the list's dimensions
get_list_dim = function(list) {
  dims = c(length(list))
  sublist = list
  # Loop through the first 10 levels of nested lists (if they exist)
  for (i in seq(10)) {
    sublist = sublist[[1]]
    # Exit the loop once we reach a non-list element
    if (!is.list(sublist)) {
      break
    }
    dims = c(dims, length(sublist))
  }
  return(dims)
}

# Function to generate n distinct colors
generate_distinct_colors <- function(n) {
  # hues <- seq(0.05, 1.05, length.out = n + 1) # Evenly space n hues
  distinct_hues <- c(0, 60, 120, 180, 240, 300)
  large_hue_set <- c(
    distinct_hues, distinct_hues + 10,
    distinct_hues + 20, distinct_hues + 30, distinct_hues + 40
  )
  if (n > length(large_hue_set)) {
    large_hue_set <- c(large_hue_set, sample(
      seq(360),
      (n - length(large_hue_set)), replace = TRUE
    ))
  }
  # Convert to HSL (HCL in R)
  hsl_colors <- hcl(h = large_hue_set[1:n], l = 70, c = 150) 
  return(hsl_colors) 
}

# Initialize a PDF to save the generated plots
pdf(out_file)

# Loop over all capital letters in the JSON data, excluding the "t" key (time)
for (letter in names(data$trajectories)[!grepl(names(data$trajectories), pattern = "Scale")]) {
  # print(letter)
  # Use the function to get dimensions of the current letter's data
  dims <- get_list_dim(data$trajectories[[letter]])
  if(max(unlist(data$trajectories[[letter]])) == 0) next
  # For debugging: print dimensions and current letter
  # print(dims)
  # print(letter)  
  if (length(dims) == 1) {  # Handle 1D vector
    # Plot the data if it's a simple vector
    colors <- generate_distinct_colors(prod(dims))
      # Determine y-axis limits
      ylims = c(min(unlist(data$trajectories[[letter]])), 
                max(unlist(data$trajectories[[letter]])))
      # Initialize an empty plot
      plot(NULL, xlim = c(0, max(data$trajectories$t)),
           ylim = ylims, xlab = "Time",
           ylab = paste("Value of", letter),
           main = paste("Plot for", letter),
           col = colors[1])

      # Add lines for each other locaiton in the first dimension
      if (is.list(data$trajectories[[letter]])) {
        for(i in seq(dims[1])){
          lines(data$trajectories$t, 
                data$trajectories[[letter]][[i]],
                col = colors[i])
        }
          legend("topright", legend = paste(letter, 0:(dims[1]-1)),
                  col = colors, lty = 1)

      } else {
        lines(data$trajectories$t, data$trajectories[[letter]], 
              col = colors[i])
        legend("topright", legend = letter, col = colors, lty = 1)
      }
      # Add a legend to the plot

  } else if (length(dims) == 2) {  # Handle 2D matrix 
    # Loop over the first dimension and plot
    # each sub-list as lines on the same plot
    for(i in seq(dims[1])){
      colors <- generate_distinct_colors(prod(dims))
      # Determine y-axis limits
      ylims = c(min(unlist(data$trajectories[[letter]][[i]])), 
                max(unlist(data$trajectories[[letter]][[i]])))

      # Initialize an empty plot
      plot(NULL, xlim = c(0, max(data$trajectories$t)), 
           ylim = ylims, xlab = 'Time',
           ylab = paste('Value of', letter, " ", "i"),
           main = paste('Plot for', letter, " ", i-1),
           col = colors[1])

      # Add lines for each subgroup in the second dimension
      for(j in 1:dims[2]) {
        lines(data$trajectories$t, data$trajectories[[letter]][[i]][[j]], 
              col = colors[j])
      }
      # Add a legend to the plot
      legend("topright",
        legend = paste(letter, i-1, 0:(dims[2]-1)),
        col = colors, lty = 1)
    }    
  } else if (length(dims) == 3) {  # Handle 3D tensor
    # Loop over the first dimension and plot
    # each sub-sub-list as lines on the same plot
    for(i in seq(dims[1])){
      colors <- generate_distinct_colors(prod(dims))
      # Determine y-axis limits
      ylims = c(min(unlist(data$trajectories[[letter]][[i]])), 
                max(unlist(data$trajectories[[letter]][[i]])))

      # Initialize an empty plot
      plot(NULL, xlim = c(0, max(data$trajectories$t)),
           ylim = ylims, xlab = 'Time',
           ylab = paste('Value of', letter, " ", "i"),
           main = paste('Plot for', letter, " ", i-1),
           col = colors[1])
      
      # For debugging: print dimensions
      # print(dims)

      # Loop through both the second and third 
      # dimensions, adding each line to the plot
      for(j in 1:dims[2]) {
        for(k in 1:dims[3]){
          lines(data$trajectories$t,
                data$trajectories[[letter]][[i]][[j]][[k]],
                col = colors[j])
        }
      }
      # Add a legend to the plot
      legend("topright",
        legend = paste(letter, i-1, 0:(dims[2]-1)),
        col = colors, lty = 1
      )
    }
  } else if (length(dims) == 4) {  # Handle 3D tensor
    # Loop over the first dimension and plot
    # each sub-sub-list as lines on the same plot
    for(i in seq(dims[1])){
      colors <- generate_distinct_colors(prod(dims))
      # Determine y-axis limits
      ylims = c(min(unlist(data$trajectories[[letter]][[i]])), 
                max(unlist(data$trajectories[[letter]][[i]])))

      # Initialize an empty plot
      plot(NULL, xlim = c(0, max(data$trajectories$t)),
           ylim = ylims, xlab = 'Time',
           ylab = paste('Value of', letter, " ", "i"),
           main = paste('Plot for', letter, " ", i-1),
           col = colors[1])
      
      # For debugging: print dimensions
      # print(dims)

      # Loop through both the second and third 
      # dimensions, adding each line to the plot
      for(j in 1:dims[2]) {
        for(k in 1:dims[3]){
          for(l in 1:dims[4]){
                      lines(data$trajectories$t,
                data$trajectories[[letter]][[i]][[j]][[k]][[l]],
                col = colors[j])
          }
        }
      }
      # Add a legend to the plot
      legend("topright",
        legend = paste(letter, i-1, 0:(dims[2]-1)),
        col = colors, lty = 1
      )
    }
  }
}

# Close the PDF file, saving all plots
dev.off()
