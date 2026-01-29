from defistream import DeFiStream

client = DeFiStream(api_key="")

# # Test the builder pattern
# query = client.erc20.transfers("DAI").network("ETH").start_block(24000000).end_block(24000100).min_amount(100)
# print(query)  # Shows QueryBuilder repr
#
# # Execute (requires actual API connection)
# transfers_df = query.as_df()
# print(transfers_df)


transfers = (
    client.native_token.transfers()
    .network("ETH")
    .start_block(24000000)
    .end_block(24000100)
    .min_amount(1.0)
    .as_dict()
)

print(transfers)
