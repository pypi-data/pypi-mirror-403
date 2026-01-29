from agno.db import sqlite


class AsyncSqliteDb(sqlite.AsyncSqliteDb):
    async def _get_table(self, table_type: str, create_table_if_not_found: Optional[bool] = False) -> Optional[Table]:
        if table_type == "sessions":
            self.session_table = await self._get_or_create_table(
                table_name=self.session_table_name,
                table_type=table_type,
                create_table_if_not_found=create_table_if_not_found,
            )
            return self.session_table

        elif table_type == "memories":
            self.memory_table = await self._get_or_create_table(
                table_name=self.memory_table_name,
                table_type="memories",
                create_table_if_not_found=create_table_if_not_found,
            )
            return self.memory_table

        elif table_type == "metrics":
            self.metrics_table = await self._get_or_create_table(
                table_name=self.metrics_table_name,
                table_type="metrics",
                create_table_if_not_found=create_table_if_not_found,
            )
            return self.metrics_table

        elif table_type == "evals":
            self.eval_table = await self._get_or_create_table(
                table_name=self.eval_table_name,
                table_type="evals",
                create_table_if_not_found=create_table_if_not_found,
            )
            return self.eval_table

        elif table_type == "knowledge":
            self.knowledge_table = await self._get_or_create_table(
                table_name=self.knowledge_table_name,
                table_type="knowledge",
                create_table_if_not_found=create_table_if_not_found,
            )
            return self.knowledge_table

        elif table_type == "culture":
            self.culture_table = await self._get_or_create_table(
                table_name=self.culture_table_name,
                table_type="culture",
                create_table_if_not_found=create_table_if_not_found,
            )
            return self.culture_table

        elif table_type == "versions":
            self.versions_table = await self._get_or_create_table(
                table_name=self.versions_table_name,
                table_type="versions",
                create_table_if_not_found=create_table_if_not_found,
            )
            return self.versions_table

        elif table_type == "traces":
            self.traces_table = await self._get_or_create_table(
                table_name=self.trace_table_name,
                table_type="traces",
                create_table_if_not_found=create_table_if_not_found,
            )
            return self.traces_table

        elif table_type == "spans":
            # Ensure traces table exists first (spans has FK to traces)
            await self._get_table(table_type="traces", create_table_if_not_found=True)
            self.spans_table = await self._get_or_create_table(
                table_name=self.span_table_name,
                table_type="spans",
                create_table_if_not_found=create_table_if_not_found,
            )
            return self.spans_table

        elif table_type == "learnings":
            self.learnings_table = await self._get_or_create_table(
                table_name=self.learnings_table_name,
                table_type="learnings",
                create_table_if_not_found=create_table_if_not_found,
            )
            return self.learnings_table

        else:
            raise ValueError(f"Unknown table type: '{table_type}'")
