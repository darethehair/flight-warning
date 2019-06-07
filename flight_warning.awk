{
distance=int($7+0.5)
bearing=int($8+0.5)
lat=$4
lon=$5

if (distance_array[bearing] < distance && distance < 500)
	{
	distance_array[bearing] = distance
	lat_array[bearing] = lat
	lon_array[bearing] = lon
	}
#print int($7+0.5), $8
}
END {
	for (bearing in distance_array)
		{
		print bearing "," distance_array[bearing] "," lat_array[bearing] "," lon_array[bearing]
		#print lon_array[bearing] "," lat_array[bearing]
		}
}
