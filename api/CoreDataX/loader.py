import pandas
import numpy
import sys
import os
import datetime
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import server
import CDX


class CsvLoader:
    def __init__(self, token):
        self.magnetics_data_cache = {}
        self.setups_data_cache = {}
        self.user_data = None
        self.token = token

    def check_columns(self, columns):
        required_columns = ["magneticReference", "frequency", "magneticFluxDensityPeak", "temperature", "volumetricLosses"]
        missing_columns = []
        for column in required_columns:
            if column not in columns:
                missing_columns.append(column)
        if len(missing_columns) > 0:
            raise ImportError(f"Missing columns: {missing_columns}")

        return True

    def check_data(self, data):
        columns_to_check = []
        for column in data:
            if column not in ["magneticReference", "setupReference", "magneticFieldWaveformType"]:
                if not isinstance(data[column].dtype, (numpy.dtypes.Float64DType, numpy.dtypes.Int64DType)):
                    columns_to_check.append(column)

        for column in columns_to_check:
            for index, value in enumerate(data[column]):
                print(value)
                try:
                    float(value)
                except ValueError:
                    raise ImportError(f"Error in column {column}, row {index}: {value} is not a number")
                # print(value.dtype)

        return True

    def get_magnetic_data(self, reference):
        if reference not in self.magnetics_data_cache:
            self.magnetics_data_cache[reference] = server.get_magnetic_data(reference, self.token)
        return self.magnetics_data_cache[reference]

    def get_setup_data(self, reference):
        if reference not in self.setups_data_cache:
            self.setups_data_cache[reference] = server.get_setup_data(reference, self.token)
        return self.setups_data_cache[reference]

    def get_user_data(self,):
        if self.user_data is None:
            self.user_data = server.get_user_data(self.token)
        return self.user_data

    def convert_data_to_cdx(self, data, where="N/A"):
        results = []
        for index, row in data.iterrows():
            magnetic_data = self.get_magnetic_data(row["magneticReference"])
            user_id = self.get_user_data()
            magnetic = magnetic_data["magnetic"]
            magnetic_index = magnetic_data["index"]
            result = CDX.OutputsCoreLossesOutput(
                coreLosses=row["volumetricLosses"] * magnetic["core"]["processedDescription"]["effectiveParameters"]["effectiveVolume"],
                methodUsed=row["setupReference"],
                origin=CDX.ResultOrigin.measurement)
            result.temperature = row["temperature"]
            result.volumetricLosses = row["volumetricLosses"]
            metadata = CDX.Metadata(
                date=str(datetime.datetime.now()),
                where=where,
                who=str(user_id),
            )
            conditions = CDX.OperatingConditions(ambientTemperature=row["temperature"])

            excitation = CDX.OperatingPointExcitation(frequency=row["frequency"])
            b_field_signal = CDX.SignalDescriptor()
            b_field_processed = CDX.Processed(
                offset=row["magneticFieldDcBias"],
                label=CDX.WaveformLabel(row["magneticFieldWaveformType"]),
                peak=row["magneticFluxDensityPeak"]
            )
            b_field_signal.processed = b_field_processed
            excitation.magneticFluxDensity = b_field_signal

            operatingPoint = CDX.OperatingPoint(
                conditions=conditions,
                excitationsPerWinding=[excitation]
            )

            # cdx.result = result
            cdx = CDX.Cdx(
                magnetic=row["magneticReference"],
                metadata=metadata,
                setup=row["setupReference"],
                operatingPoint=operatingPoint,
                result=result,
            )
            
            data = {
                'cdx': cdx.to_dict(),
                'magnetic_index': magnetic_index,
                'user_id': user_id,
                'volumetric_losses': row["volumetricLosses"],
                'frequency': row["frequency"],
                'temperature': row["temperature"],
                'magnetic_flux_density_peak': row["magneticFluxDensityPeak"],
                'created_at': str(datetime.datetime.now()),
                'updated_at': str(datetime.datetime.now())
            }
            results.append(data)
        return results

    def load(self, filepath):
        data = pandas.read_csv(filepath)
        self.check_columns(data.columns)
        self.check_data(data)
        data_to_insert = self.convert_data_to_cdx(data)
        print(len(data_to_insert))
        server.insert_data(data_to_insert)


class CdxLoader:
    def __init__(self, token):
        self.user_data = None
        self.token = token

    def get_user_data(self,):
        if self.user_data is None:
            self.user_data = server.get_user_data(self.token)
        return self.user_data

    def convert_cdx_to_dict(self, data, where="N/A"):
        # TODO
        pass


if __name__ == '__main__':  # pragma: no cover

    if len(sys.argv) < 2:
        raise AttributeError("Missing token. Execution syntax is: 'python3 csv_loader.py token file.csv/cdx'")
    if len(sys.argv) < 3:
        raise AttributeError("Missing CSV/CDX file. Execution syntax is: 'python3 csv_loader.py token file.csv/cdx'")
    token = sys.argv[1]
    filepath = sys.argv[2]
    if os.path.splitext(filepath)[1].lower() == '.csv':
        csv_loader = CsvLoader(token)
        csv_loader.load(filepath)
    elif os.path.splitext(filepath)[1].lower() == '.cdx':
        cdx_loader = CdxLoader(token)
        cdx_loader.load(filepath)
    else:
        raise ValueError(f"Unknown file format: {filepath}")
