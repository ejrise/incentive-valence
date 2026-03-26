#!/bin/bash

base_dir=/path/to/base/dir

# Loop over the subject folders
#!/bin/bash

# Function to calculate the standard deviation
calculate_standard_deviation() {
    values=("$@")
    local sum=0
    local sum_sq=0
    local count=${#values[@]}

    for value in "${values[@]}"; do
        sum=$(echo "$sum + $value" | bc -l)
        sum_sq=$(echo "$sum_sq + ($value * $value)" | bc -l)
    done

    if (( count > 1 )); then
        mean=$(echo "$sum / $count" | bc -l)
        variance=$(echo "($sum_sq / $count) - ($mean * $mean)" | bc -l)
        stddev=$(echo "sqrt($variance)" | bc -l)
        stderr=$(echo "$stddev / sqrt($count)" | bc -l)
        echo "$stderr"
    else
        echo "0"
    fi
}

# Loop over the subject folders
for i in $(seq -w 1 28); do
    folder=$base_dir/"sub-$i"
    fd_file="$folder/fd.txt"

    # Check if the fd.txt file exists
    if [[ -f $fd_file ]]; then
        # Initialize variables for calculating the average
        sum=0
        count=0
        max_value=0
        values=()

        # Read through the fd.txt file
        while read -r value; do
            # Update the maximum value
            if (( $(echo "$value > $max_value" | bc -l) )); then
                max_value=$value
            fi
            # Update the sum and count for average calculation
            sum=$(echo "$sum + $value" | bc -l)
            count=$((count + 1))
            values+=("$value")
        done < "$fd_file"

        # Calculate the average and standard error
        if (( count > 0 )); then
            average=$(echo "$sum / $count" | bc -l)
            stderr=$(calculate_standard_deviation "${values[@]}")
            printf "In %s, Maximum value: %f, Average value: %f, Standard error: %f\n" "$fd_file" "$max_value" "$average" "$stderr"
        else
            echo "File $fd_file is empty."
        fi
    else
        echo "File $fd_file does not exist."
    fi
done

