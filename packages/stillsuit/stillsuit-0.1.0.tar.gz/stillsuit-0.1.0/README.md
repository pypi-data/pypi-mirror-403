# stillsuit

A place to store the buffers

## Example

```bash
e1-056827:offline crh184$ cat merge.sh 
# First stage clustering
stillsuit-merge-reduce \
	--config-schema fake_cbc.yaml \
	--clustering-column network_chisq_weighted_snr \
	--clustering-window 0.1 \
	--db-to-insert-into cluster1.sqlite \
	--verbose \
        --dbs out.sqlite 

# Second stage clustering
stillsuit-merge-reduce \
	--config-schema fake_cbc.yaml \
	--clustering-column likelihood \
	--clustering-window 4.0 \
	--db-to-insert-into cluster2.sqlite \
	--verbose \
        --dbs cluster1.sqlite 
```

