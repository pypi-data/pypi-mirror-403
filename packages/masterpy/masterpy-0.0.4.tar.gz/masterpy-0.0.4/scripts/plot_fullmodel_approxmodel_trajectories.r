#!/usr/bin/env Rscript

# Load necessary libraries
library(ggplot2)
library(rjson)

# Command line arguments
args <- commandArgs(trailingOnly = TRUE)

# Reading JSON files
json1 <- fromJSON(file = args[1])
json2 <- fromJSON(file = args[2])

plot_time_series <- function(json_data1, json_data2, pdf_filename) {

    if( "trajectories" %in% names(json_data1) ){
        json_data1 = json_data1$trajectories[[1]]
    }
    if( "trajectories" %in% names(json_data2) ){
        json_data2 = json_data2$trajectories[[1]]
    }

    Time <- SumEI <- Dataset <- Location <- NULL
    time_points <- json_data1$t
    num_time <- length(time_points)
    num_locations <- length(json_data1$Infected)
    num_infect_stages <- length(json_data1$Infected[[1]][[1]])

    # print(names(json_data1))

    # Create a PDF for plots
    pdf(pdf_filename, width = 10, height = 6)

    # Initialize a list to store data for the combined plot
    all_locations_data <- list()

    # home location
    for (i in 1:num_locations) {
      
        # initialize sums of compartment sizes, indexed by time
        sum_data1 <- rep(0, num_time)
        sum_data2 <- rep(0, num_time)

        # current location
        for (j in 1:num_locations) {
            sum_data1 <- sum_data1 + json_data1$Contagious[[i]][[j]][[1]]
            sum_data2 <- sum_data2 + json_data2$Contagious[[i]][[j]][[1]]

            for (k in 1:num_infect_stages) {
                sum_data1 <- sum_data1 + json_data1$Infected[[i]][[j]][[k]][[1]]
                sum_data2 <- sum_data2 + json_data2$Infected[[i]][[j]][[k]][[1]]
            }
        }

        # print("remove this!")
        # sum_data1 = 3 * sum_data1

        # cat("JSON dataset 1: ", args[1], "\n", sep="")
        # cat("  sum infected[", i, "] = ", sum(sapply(json_data1$Infected[[i]], unlist)), "\n", sep="")
        # cat("  sum contagious[", i, "] = ", sum(sapply(json_data1$Contagious[[i]], unlist)), "\n", sep="")
        # cat("JSON dataset 2: ", args[2], "\n", sep="")
        # cat("  sum infected[", i, "] = ", sum(sapply(json_data2$Infected[[i]], unlist)), "\n", sep="")
        # cat("  sum contagious[", i, "] = ", sum(sapply(json_data2$Contagious[[i]], unlist)), "\n", sep="")
        # cat("\n")

        # data frame for plotting home-location i
        plot_data <- data.frame(
            Time = rep(time_points, 2),
            SumEI = c(sum_data1, sum_data2),
            Dataset = factor(rep(c("Dataset 1", "Dataset 2"),
                each = length(time_points)
            )),
            Location = factor(rep(i, 2 * length(time_points)))
        )

        # Add this plot_data to the list
        all_locations_data[[i]] <- plot_data

        # Create plot
        p <- ggplot(plot_data, aes(
            x = Time, y = SumEI,
            color = Dataset, linetype = Dataset
        )) +
            geom_line() +
            labs(
                title = paste("Time Series for Location", i-1),
                x = "Time",
                y = "Sum of Infected and Contagious"
            ) +
            theme_minimal() +
            scale_color_manual(values = c(
                "Dataset 1" = "blue",
                "Dataset 2" = "red"
            )) +
            scale_linetype_manual(values = c(
                "Dataset 1" = "solid",
                "Dataset 2" = "dashed"
            ))

        # Draw plot
        print(p)
    }

    # Combined plot for all locations
    combined_data <- do.call(rbind, all_locations_data)
    p_combined <- ggplot(combined_data, aes(
        x = Time, y = SumEI,
        color = Dataset, linetype = Dataset, group = interaction(Dataset, Location)
        ))  +
        geom_line() +
        labs(
            title = "Combined Time Series for All Locations",
            x = "Time",
            y = "Sum of Infected and Contagious"
        ) +
        theme_minimal() +
        scale_color_manual(values = c(
            "Dataset 1" = "blue",
            "Dataset 2" = "red"
        )) +
        scale_linetype_manual(values = c(
            "Dataset 1" = "solid",
            "Dataset 2" = "dashed"
        ))

    # Draw the combined plot
    print(p_combined)

    # Close the PDF device
    dev.off()
}

plot_time_series(json1, json2, args[3])
