#RCode for PlotmyRide
#By David Greis

#input data
dir = "/Users/dgreis/Downloads/"
infile = paste(dir,"strava.csv",sep="")
rdat = read.csv(infile,header=TRUE,sep=",",stringsAsFactors=FALSE)

#Remove duplicates; convert averageSpeed to numeric
dat = unique(rdat)
dat[,9] = as.numeric(dat[,9])

#Alert if there is more than one missing value for aspeed
missalert = length(which(is.na(dat$averageSpeed)))
if (missalert > 1){
	print("More than one missing aspeed value")
	makeerror
}
miss = which(is.na(dat$averageSpeed))
dat = dat[-miss,]

#Remove outliers
iqr_3 = 3*IQR(dat$averageSpeed)
ubound = quantile(dat$averageSpeed)[4] + iqr_3
lbound = quantile(dat$averageSpeed)[1] - iqr_3

outlier = which(dat$averageSpeed>ubound)
if (length(outlier) > 1){
	print("More than one super outlier")
	makeerror
}
dat = dat[-outlier,]



